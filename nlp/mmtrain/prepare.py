"""Lossless token cache plus coverage, length, duplicate and class reports."""

import json
from pathlib import Path

import numpy as np
import torch

from .chunks import make_chunks
from .data import LABELS, load_cache, load_sources, sha


def prepare(config):
    from transformers import AutoTokenizer
    root = Path(config['run_dir'])
    if (root/'token_cache_manifest.json').exists():
        cache = load_cache(config)
        print('Reusing token cache:',{k:len(v) for k,v in cache['splits'].items()},flush=True)
        return
    for name,digest in config['inputs'].items():
        if sha(Path(config['data_dir'])/name) != digest:
            raise ValueError('Input changed after configuration was frozen')
    sources, labels, splits, excluded = load_sources(config['data_dir'])
    tokenizer = AutoTokenizer.from_pretrained(config['model_id'],revision=config['revision'])
    records, split_report = {}, {}
    for split, ids in splits.items():
        lengths, windows = [], []
        for i,uid in enumerate(ids):
            chunks, stats = make_chunks(sources[uid],tokenizer,config['chunk_length'],config['overlap'])
            row = {k:sources[uid][k] for k in ('dataset','source_id','student_id','conversation_id','input_sha256')}
            row.update(chunks=chunks,labels=[float(labels[uid][k]=='true') for k in LABELS],stats=stats)
            records[uid] = row
            lengths.append(stats['single_input_tokens'])
            windows.append(stats['chunks'])
            if (i+1)%250==0:
                print(split,'tokenized',i+1,'/',len(ids),flush=True)
        split_report[split] = {'rows':len(ids),'tokens_percentiles':dict(zip(('p50','p90','p95','p99','max'),
                                  np.percentile(lengths,[50,90,95,99,100]).astype(int).tolist(),strict=True)),
                              'over_8192':sum(n>8192 for n in lengths),'max_chunks':max(windows),
                              'total_chunks':sum(windows),
                              'positives':{key:int(sum(records[uid]['labels'][j] for uid in ids))
                                           for j,key in enumerate(LABELS)}}
    cache = {'records':records,'splits':splits,'excluded':excluded,'identity':config['identity']}
    temp = root/'tokenized.tmp'
    torch.save(cache,temp)
    temp.replace(root/'tokenized.pt')
    manifest = {'identity':config['identity'],'sha256':sha(root/'tokenized.pt'),'splits':split_report,
                'excluded_exact_duplicates':excluded,'original_csv_rows':len(sources),
                'kept_rows':len(records),'all_tokens_processed':True,'max_chunks_cap':None}
    (root/'token_cache_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k!='excluded_exact_duplicates'},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    import sys
    prepare(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
