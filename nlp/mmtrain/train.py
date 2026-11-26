"""Full encoder fine-tuning, validation-only selection, exact optimizer-boundary resume."""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from .checkpoint import load, restore_rng, rng_state, save
from .data import load_cache
from .metrics import choose_thresholds, evaluate
from .runtime import initialize, loss_group, predict


def epoch_ids(ids, records, epoch, seed):
    generator = torch.Generator().manual_seed(seed+epoch)
    ordered = sorted(ids,key=lambda uid:records[uid]['stats']['chunks'])
    buckets = [ordered[i:i+64] for i in range(0,len(ordered),64)]
    result = []
    for index in torch.randperm(len(buckets),generator=generator).tolist():
        bucket = buckets[index]
        result.extend(bucket[j] for j in torch.randperm(len(bucket),generator=generator).tolist())
    return result


def train(config, smoke=False):
    cache = load_cache(config)
    records, splits = cache['records'],cache['splits']
    root = Path(config['run_dir'])
    model, optimizer = initialize(config)
    train_ids = splits['train']
    prevalence = np.mean([records[uid]['labels'] for uid in train_ids],axis=0)
    weights = np.clip((1-prevalence)/np.maximum(prevalence,1/len(train_ids)),.5,5)
    pos_weight = torch.tensor(weights,device='cuda',dtype=torch.float32) if config['class_weights'] else None
    if smoke:
        chosen = sorted(train_ids,key=lambda uid:records[uid]['stats']['chunks'])
        chosen = list(dict.fromkeys(chosen[:2]+chosen[-1:]))
        started = time.monotonic()
        model.train()
        optimizer.zero_grad(set_to_none=True)
        loss = loss_group(model,records,chosen,config['record_batch'],pos_weight)
        if not any(p.grad is not None and torch.count_nonzero(p.grad).item() for p in model.encoder.parameters()):
            raise ValueError('Encoder gradients missing')
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        optimizer.step()
        torch.cuda.synchronize()
        report = {'loss':loss,'sample_rows':len(chosen),
                  'max_sample_chunks':max(records[u]['stats']['chunks'] for u in chosen),
                  'seconds':time.monotonic()-started,'peak_vram_gib':torch.cuda.max_memory_allocated()/2**30,
                  'note':'Smoke includes the longest train conversation; weights are NOT used for full training.'}
        (root/'smoke_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
        return
    steps_per_epoch = math.ceil(len(train_ids)/config['effective_batch'])
    total = steps_per_epoch*config['epochs']
    warmup = max(1,int(total*.1))
    def multiplier(step):
        return step/warmup if step<warmup else .5*(1+math.cos(math.pi*(step-warmup)/max(1,total-warmup)))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer,multiplier)
    epoch,offset,step,best,bad_epochs,best_file = 0,0,0,-1.,0,None
    latest = root/'latest.pt'
    if latest.exists():
        state = load(latest,config['identity'])
        model.load_state_dict(state['model'])
        optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler'])
        epoch,offset,step,best,bad_epochs = [state[k] for k in ('epoch','offset','step','best','bad_epochs')]
        best_file = state['best_file']
        restore_rng(state['rng'])
        del state
        print('Resuming optimizer step',step,'epoch',epoch,'next row offset',offset,flush=True)
    def checkpoint(next_epoch, next_offset):
        save(latest,{'identity':config['identity'],'model':model.state_dict(),'optimizer':optimizer.state_dict(),
                     'scheduler':scheduler.state_dict(),'rng':rng_state(),'epoch':next_epoch,'offset':next_offset,
                     'step':step,'best':best,'bad_epochs':bad_epochs,'best_file':best_file})
        print('Drive checkpoint committed:',step,flush=True)
    if bad_epochs >= config['patience']:
        print('Early stopping already satisfied; using best.pt',flush=True)
        return
    while epoch<config['epochs']:
        ordered = epoch_ids(train_ids,records,epoch,config['seed'])
        model.train()
        started = time.monotonic()
        for start in range(offset,len(ordered),config['effective_batch']):
            group = ordered[start:start+config['effective_batch']]
            optimizer.zero_grad(set_to_none=True)
            loss = loss_group(model,records,group,config['record_batch'],pos_weight)
            norm = torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            if not torch.isfinite(norm):
                raise ValueError('Nonfinite gradient norm')
            optimizer.step()
            scheduler.step()
            step += 1
            if step%10==0:
                print('epoch',epoch+1,'step',step,'rows',start+len(group),'/',len(ordered),
                      'loss',round(loss,4),'elapsed sec',round(time.monotonic()-started,1),flush=True)
            if step%config['save_steps']==0 and start+len(group)<len(ordered):
                checkpoint(epoch,start+len(group))
        target, probabilities, seconds = predict(model,records,splits['valid'],config['record_batch'])
        thresholds = choose_thresholds(target,probabilities)
        report = evaluate(target,probabilities,thresholds)
        report.update(epoch=epoch+1,optimizer_step=step,predict_seconds=seconds,
                      peak_vram_gib=torch.cuda.max_memory_allocated()/2**30)
        score = report['mean_label_macro_f1']
        if score>best:
            best,bad_epochs = score,0
            best_file = f'best_step_{step}.pt'
            save(root/best_file,{'identity':config['identity'],'model':model.state_dict(),
                                 'thresholds':thresholds,'valid_report':report})
            (root/'best_valid_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        else:
            bad_epochs += 1
        with (root/'training_log.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(report)+'\n')
        print(json.dumps(report,indent=2),flush=True)
        epoch,offset = epoch+1,0
        checkpoint(epoch,0)
        if bad_epochs>=config['patience']:
            print('Early stopping on VALID only',flush=True)
            break
    print('Training complete; committed best model and thresholds:',root/best_file,flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--smoke',action='store_true')
    args = parser.parse_args()
    train(json.loads(Path(args.config).read_text(encoding='utf-8')),args.smoke)
