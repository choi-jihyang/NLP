"""CPU invariants: lossless chunking, role masks, bag gradients and exact resume."""

import contextlib
import copy
import csv
import gzip
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch
from torch import nn

from mmtrain.checkpoint import load, restore_rng, rng_state, save
from mmtrain.chunks import make_chunks, special_wrapper
from mmtrain.data import LABELS, load_sources, stable
from mmtrain.metrics import choose_thresholds, evaluate
from mmtrain.model import DialogueClassifier
from mmtrain.runtime import loss_group
from mmtrain.train import epoch_ids
from mmtrain.train import train as run_training


class Tokenizer:
    def encode(self,text,add_special_tokens=False,**kwargs):
        ids = [ord(c)%500+3 for c in text]
        return [1,*ids,2] if add_special_tokens else ids

    def __call__(self,text,**kwargs):
        ids = self.encode(text,add_special_tokens=True)
        return {'input_ids':ids,'special_tokens_mask':[1]+[0]*(len(ids)-2)+[1]}


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(504,8)
        self.linear = nn.Linear(8,8)
        self.dropout = nn.Dropout(.15)

    def forward(self,input_ids,attention_mask):
        return SimpleNamespace(last_hidden_state=self.dropout(self.linear(self.embedding(input_ids))))


def source(index='x', message='My own work'):
    row = dict(dataset='studychat',source_id=index,student_id='s'+index,conversation_id='c'+index,
               message=message,history=[{'role':'assistant','content':'AI solution'},
               {'role':'student','content':'Past student draft'}],input_verified=True)
    row['input_sha256'] = stable({k:row[k] for k in ('message','history')})
    return row


class HierarchicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_all_tokens_and_long_current_preserved_once(self):
        record = source(message='LAST_CURRENT_TOKEN_'*500)
        chunks, stats = make_chunks(record,Tokenizer(),128,16)
        self.assertGreater(len(chunks),70)
        self.assertTrue(all(len(c['input_ids'])<=128 for c in chunks))
        self.assertEqual(sum(sum(c['owner_mask']) for c in chunks),stats['tokens'])
        self.assertEqual(sum(sum(c['current_mask']) for c in chunks),len(record['message']))
        self.assertEqual(chunks[-1]['end'],stats['tokens'])
        current_ids = [t for c in chunks for t,m in zip(c['input_ids'],c['current_mask'],strict=True) if m]
        self.assertEqual(current_ids,Tokenizer().encode(record['message']))

    def test_role_masks_exclude_assistant_and_metadata(self):
        record = source()
        chunks, stats = make_chunks(record,Tokenizer(),64,8)
        expected = len(record['message'])+len(record['history'][1]['content'])
        self.assertEqual(stats['student_tokens'],expected)
        self.assertEqual(sum(sum(c['student_mask']) for c in chunks),expected)
        self.assertTrue(all(not c['student_mask'][0] and not c['student_mask'][-1] for c in chunks))
        self.assertEqual(special_wrapper(Tokenizer()),([1],[2]))

    def test_limits_empty_current_and_overlap(self):
        for length,overlap in ((8193,2),(32,30),(15,0)):
            with self.assertRaises(ValueError):
                make_chunks(source(),Tokenizer(),length,overlap)
        chunks,stats = make_chunks(source(message=''),Tokenizer(),128,0)
        self.assertEqual(stats['current_tokens'],0)
        self.assertEqual(sum(sum(c['owner_mask']) for c in chunks),stats['tokens'])

    def test_labels_cannot_enter_token_features(self):
        record = source()
        expected = make_chunks(record,Tokenizer(),128,16)
        record.update(labels={'secret':'DO_NOT_LEAK'},rationale='SECRET')
        self.assertEqual(expected,make_chunks(record,Tokenizer(),128,16))

    def test_checkpointed_integer_inputs_keep_encoder_gradients(self):
        torch.manual_seed(42)
        model = DialogueClassifier(TinyEncoder(),8,0,window_batch=2)
        reference = copy.deepcopy(model)
        chunks,_ = make_chunks(source(),Tokenizer(),64,8)
        model.train()
        reference.train()
        torch.manual_seed(77)
        model(chunks).sum().backward()
        torch.manual_seed(77)
        with patch('mmtrain.model.checkpoint',lambda function,*args,**kw:function(*args)):
            reference(chunks).sum().backward()
        self.assertGreater(float(model.encoder.embedding.weight.grad.abs().sum()),0.)
        for actual,expected in zip(model.parameters(),reference.parameters(),strict=True):
            torch.testing.assert_close(actual.grad,expected.grad,atol=1e-6,rtol=1e-5)

    def test_multiple_bags_equal_separate_in_eval(self):
        model = DialogueClassifier(TinyEncoder(),8,0,window_batch=3).eval()
        bags = [make_chunks(source(str(i),message='text'*i),Tokenizer(),64,8)[0] for i in (1,3)]
        with torch.no_grad():
            actual = model.forward_many(bags)
            expected = torch.stack([model(bag) for bag in bags])
        torch.testing.assert_close(actual,expected)
        _, attention = model(bags[1],return_attention=True)
        for weight,chunk in zip(attention['student'],bags[1],strict=True):
            if not sum(chunk['student_mask']):
                self.assertEqual(float(weight.detach()),0.)

    def test_loss_is_per_record_not_per_window(self):
        model = DialogueClassifier(TinyEncoder(),8,0,window_batch=2,dropout=0).eval()
        records = {str(i):{'chunks':make_chunks(source(str(i),message='text'*i),Tokenizer(),64,8)[0],
                           'labels':[float(i%2),0.]} for i in (1,12)}
        ids = list(records)
        loss = loss_group(model,records,ids,2)
        with torch.no_grad():
            expected = nn.BCEWithLogitsLoss()(model.forward_many([records[u]['chunks'] for u in ids]),
                                            torch.tensor([records[u]['labels'] for u in ids]))
        self.assertAlmostEqual(loss,float(expected),places=6)

    def test_optimizer_and_rng_resume_exact(self):
        torch.manual_seed(42)
        model = DialogueClassifier(TinyEncoder(),8,0,window_batch=2)
        optimizer = torch.optim.AdamW(model.parameters(),lr=.001)
        chunks,_ = make_chunks(source(),Tokenizer(),64,8)
        records = {'x':{'chunks':chunks,'labels':[1.,0.]}}
        def step(m,opt):
            m.train()
            opt.zero_grad(set_to_none=True)
            loss_group(m,records,['x'],1)
            opt.step()
        step(model,optimizer)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'latest.pt'
            save(path,{'identity':'fixed','model':model.state_dict(), 'optimizer':optimizer.state_dict(),
                       'rng':rng_state()})
            step(model,optimizer)
            fresh = DialogueClassifier(TinyEncoder(),8,0,window_batch=2)
            other = torch.optim.AdamW(fresh.parameters(),lr=.001)
            state = load(path,'fixed')
            fresh.load_state_dict(state['model'])
            other.load_state_dict(state['optimizer'])
            restore_rng(state['rng'])
            step(fresh,other)
            for actual,expected in zip(fresh.parameters(),model.parameters(),strict=True):
                torch.testing.assert_close(actual,expected,atol=0,rtol=0)
            with self.assertRaises(ValueError):
                load(path,'changed')

    def test_threshold_metrics_and_epoch_reconstruction(self):
        target = [[0,0],[1,1],[0,1],[1,0]]
        probabilities = [[.1,.1],[.8,.8],[.2,.9],[.9,.2]]
        thresholds = choose_thresholds(target,probabilities)
        self.assertEqual(evaluate(target,probabilities,thresholds)['mean_label_macro_f1'],1.)
        records = {str(i):{'stats':{'chunks':i%3+1}} for i in range(100)}
        a = epoch_ids(list(records),records,0,42)
        self.assertEqual(a,epoch_ids(list(records),records,0,42))
        self.assertEqual(set(a),set(records))
        self.assertNotEqual(a,epoch_ids(list(records),records,1,42))

    def test_training_loop_resume_and_validation_only_selection(self):
        records = {}
        for i in range(9):
            chunks,stats = make_chunks(source(str(i),message='draft '+str(i)),Tokenizer(),96,8)
            records[str(i)] = {'chunks':chunks,'stats':stats,'labels':[float(i%2),float((i+1)%2)]}
        cache = {'records':records,'splits':{'train':list(records)[:6],'valid':['6','7'],'test':['8']}}
        def initialize(config):
            torch.manual_seed(config['seed'])
            model = DialogueClassifier(TinyEncoder(),8,0,window_batch=2)
            return model,torch.optim.AdamW(model.parameters(),lr=.001)
        with tempfile.TemporaryDirectory() as directory:
            base,resumed = Path(directory)/'base',Path(directory)/'resumed'
            base.mkdir()
            resumed.mkdir()
            config = dict(run_dir=str(base),identity='fixed',seed=42,effective_batch=2,record_batch=2,
                          class_weights=False,epochs=2,save_steps=1,patience=99)
            with (patch('mmtrain.train.load_cache',return_value=cache),
                  patch('mmtrain.train.initialize',side_effect=initialize),
                  patch('torch.cuda.max_memory_allocated',return_value=0),
                  contextlib.redirect_stdout(io.StringIO())):
                run_training(config)
                uninterrupted = load(base/'latest.pt','fixed')
                calls = 0
                def interrupt(*args,**kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == 3:
                        raise KeyboardInterrupt()
                    return loss_group(*args,**kwargs)
                config['run_dir'] = str(resumed)
                with patch('mmtrain.train.loss_group',side_effect=interrupt),self.assertRaises(KeyboardInterrupt):
                    run_training(config)
                partial = load(resumed/'latest.pt','fixed')
                self.assertEqual((partial['epoch'],partial['offset'],partial['step']),(0,4,2))
                self.assertIsNone(partial['best_file'])
                run_training(config)
                result = load(resumed/'latest.pt','fixed')
            self.assertEqual((result['step'],result['epoch']),(6,2))
            self.assertEqual(result['best_file'],uninterrupted['best_file'])
            for key in result['model']:
                torch.testing.assert_close(result['model'][key],uninterrupted['model'][key],atol=0,rtol=0)
            best = load(resumed/result['best_file'],'fixed')
            self.assertEqual(best['valid_report']['rows'],2)

    def test_sources_hash_duplicates_and_group_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            originals = [source('0','same'),source('1','same'),source('2','other'),source('3','train')]
            fields = ['dataset','source_id','student_id','conversation_id','is_learning_context',*LABELS,'status']
            for split,indexes in (('train',[0,3]),('valid',[2]),('test',[1])):
                with (root/f'{split}_ok.csv').open('w',encoding='utf-8',newline='') as stream:
                    writer = csv.DictWriter(stream,fieldnames=fields)
                    writer.writeheader()
                    for i in indexes:
                        writer.writerow({**{k:originals[i][k] for k in fields[:4]},
                                         'is_learning_context':'true',**dict.fromkeys(LABELS,'false'),'status':'ok'})
            with gzip.open(root/'inputs.jsonl.gz','wt',encoding='utf-8') as stream:
                for original in originals:
                    stream.write(json.dumps(original)+'\n')
            _,_,splits,excluded = load_sources(root)
            self.assertEqual(splits['train'],['studychat:3'])
            self.assertEqual(excluded[0]['id'],'studychat:0')
            content = (root/'valid_ok.csv').read_text(encoding='utf-8')
            (root/'valid_ok.csv').write_text(content.replace('s2','s1'),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'overlaps splits'):
                load_sources(root)


if __name__=='__main__':
    unittest.main()
