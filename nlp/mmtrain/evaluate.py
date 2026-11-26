"""Final held-out evaluation with fixed validation thresholds and per-row predictions."""

import json
from pathlib import Path

import numpy as np

from .checkpoint import load
from .data import load_cache, sha
from .metrics import evaluate
from .runtime import initialize, predict


def run(config):
    root = Path(config['run_dir'])
    committed = load(root/'latest.pt',config['identity'])
    best_name = committed['best_file']
    if best_name is None:
        raise ValueError('No completed validation checkpoint; finish training first')
    del committed
    best_path, report_path = root/best_name,root/'test_report.json'
    digest = sha(best_path)
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding='utf-8'))
        if report['checkpoint_sha256'] != digest or report['identity'] != config['identity']:
            raise ValueError('Existing test report is for a different checkpoint/config')
        print('Reusing completed test report',json.dumps(report,indent=2))
        return
    state = load(best_path,config['identity'])
    cache = load_cache(config)
    model,_ = initialize(config)
    model.load_state_dict(state['model'])
    records, ids = cache['records'],cache['splits']['test']
    target, probabilities, seconds = predict(model,records,ids,config['record_batch'])
    report = evaluate(target,probabilities,state['thresholds'])
    prevalence = np.mean([records[u]['labels'] for u in cache['splits']['train']],axis=0)
    report['majority_baseline'] = evaluate(target,np.tile(prevalence,(len(ids),1)),[.5,.5])
    report.update(identity=config['identity'],checkpoint_sha256=digest,predict_seconds=seconds,
                  rows_per_second=len(ids)/max(seconds,1e-9),valid_report=state['valid_report'])
    temp = root/'test_predictions.tmp'
    with temp.open('w',encoding='utf-8') as stream:
        for uid,truth,prob in zip(ids,target,probabilities,strict=True):
            stream.write(json.dumps({'id':uid,'input_sha256':records[uid]['input_sha256'],
                'target':truth.tolist(),'probabilities':prob.tolist(),
                'prediction':(prob>=np.asarray(state['thresholds'])).tolist()})+'\n')
    temp.replace(root/'test_predictions.jsonl')
    temporary = report_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report,indent=2),encoding='utf-8')
    temporary.replace(report_path)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    import sys
    run(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
