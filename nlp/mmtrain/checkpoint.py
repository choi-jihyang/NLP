"""Atomic Drive checkpoints with optimizer and RNG state, only at optimizer boundaries."""

import os
from pathlib import Path

import torch


def save(path, state):
    path = Path(path)
    temporary = path.with_suffix('.tmp')
    with temporary.open('wb') as stream:
        torch.save(state,stream)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def rng_state():
    return {'cpu':torch.get_rng_state(), 'cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def restore_rng(state):
    torch.set_rng_state(state['cpu'])
    if state['cuda'] and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state['cuda'])


def load(path, identity):
    value = torch.load(path,map_location='cpu',weights_only=True)
    if value['identity'] != identity:
        raise ValueError('Checkpoint config/model/data/code identity differs')
    return value
