"""GPU initialization, equal-record loss and prediction independent of test selection."""

import contextlib
import time

import numpy as np
import torch
from torch import nn

from .model import build_model


def initialize(config):
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError('A100/H100 BF16 GPU required')
    torch.manual_seed(config['seed'])
    torch.cuda.manual_seed_all(config['seed'])
    print('GPU:',torch.cuda.get_device_name(0),'window batch:',config['window_batch'],
          'record batch:',config['record_batch'],flush=True)
    model = build_model(config).cuda()
    encoder_ids = {id(p) for p in model.encoder.parameters()}
    optimizer = torch.optim.AdamW([
        {'params':[p for p in model.parameters() if id(p) in encoder_ids], 'lr':config['encoder_lr']},
        {'params':[p for p in model.parameters() if id(p) not in encoder_ids], 'lr':config['head_lr']}],
        weight_decay=.01)
    return model,optimizer


def amp(model):
    return torch.autocast('cuda',dtype=torch.bfloat16) if next(model.parameters()).is_cuda else contextlib.nullcontext()


def loss_group(model, records, ids, record_batch, pos_weight=None):
    """One equally weighted loss per conversation, regardless of number of windows."""
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    device = next(model.parameters()).device
    total = 0.
    for start in range(0,len(ids),record_batch):
        current = ids[start:start+record_batch]
        target = torch.tensor([records[uid]['labels'] for uid in current],device=device)
        with amp(model):
            logits = model.forward_many([records[uid]['chunks'] for uid in current])
            loss = criterion(logits,target)*(len(current)/len(ids))
        if not torch.isfinite(loss):
            raise ValueError('Nonfinite training loss')
        loss.backward()
        total += float(loss.detach())
    return total


def predict(model, records, ids, record_batch):
    model.eval()
    probabilities, target = [], []
    if next(model.parameters()).is_cuda:
        torch.cuda.synchronize()
    started = time.monotonic()
    with torch.inference_mode():
        for start in range(0,len(ids),record_batch):
            current = ids[start:start+record_batch]
            with amp(model):
                logits = model.forward_many([records[uid]['chunks'] for uid in current])
            probabilities.extend(torch.sigmoid(logits.float()).cpu().tolist())
            target.extend(records[uid]['labels'] for uid in current)
    if next(model.parameters()).is_cuda:
        torch.cuda.synchronize()
    return np.asarray(target),np.asarray(probabilities),time.monotonic()-started
