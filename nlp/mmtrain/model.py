"""Full-token window encoder plus current-conditioned context and student pooling."""

import torch
from torch import nn
from torch.utils.checkpoint import checkpoint


def pad_windows(chunks, pad_id, device):
    length = max(len(c['input_ids']) for c in chunks)
    result = {}
    for key in ('input_ids','student_mask','current_mask','owner_mask'):
        fill = pad_id if key=='input_ids' else 0
        result[key] = torch.tensor([c[key]+[fill]*(length-len(c[key])) for c in chunks],device=device)
    result['attention_mask'] = torch.tensor([[1]*len(c['input_ids'])+[0]*(length-len(c['input_ids']))
                                            for c in chunks],device=device)
    return result


class DialogueClassifier(nn.Module):
    def __init__(self, encoder, hidden, pad_id, window_batch=2, dropout=.1):
        super().__init__()
        self.encoder, self.pad_id, self.window_batch = encoder, pad_id, window_batch
        self.position = nn.Linear(3,hidden)
        self.context_key = nn.Linear(hidden,hidden)
        self.student_key = nn.Linear(hidden,hidden)
        self.query_key = nn.Linear(hidden,hidden)
        self.context_score = nn.Linear(hidden,1)
        self.student_score = nn.Linear(hidden,1)
        self.heads = nn.ModuleList([nn.Sequential(nn.LayerNorm(hidden*4),nn.Dropout(dropout),
                                    nn.Linear(hidden*4,hidden),nn.GELU(),nn.Linear(hidden,1)) for _ in range(2)])

    def encode_pool(self, ids, attention, student, current, owner):
        hidden = self.encoder(input_ids=ids,attention_mask=attention).last_hidden_state.float()
        def pool(mask):
            mask = mask.unsqueeze(-1).to(hidden.dtype)
            return (hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
        return torch.stack([pool(owner),pool(student),pool(current)],dim=1)

    def encode_chunks(self, chunks):
        device = next(self.parameters()).device
        features = []
        for start in range(0,len(chunks),self.window_batch):
            batch = pad_windows(chunks[start:start+self.window_batch],self.pad_id,device)
            args = [batch[k] for k in ('input_ids','attention_mask','student_mask','current_mask','owner_mask')]
            if self.training and torch.is_grad_enabled():
                features.append(checkpoint(self.encode_pool,*args,use_reentrant=False,preserve_rng_state=True))
            else:
                features.append(self.encode_pool(*args))
        return torch.cat(features).float()

    def classify(self, chunks, features, return_attention=False):
        device = features.device
        current_counts = torch.tensor([sum(c['current_mask']) for c in chunks],device=device,dtype=torch.float32)
        student_counts = torch.tensor([sum(c['student_mask']) for c in chunks],device=device,dtype=torch.float32)
        owner_counts = torch.tensor([sum(c['owner_mask']) for c in chunks],device=device,dtype=torch.float32)
        query = (features[:,2]*current_counts[:,None]).sum(0)/current_counts.sum().clamp(min=1)
        positions = torch.stack([torch.arange(len(chunks),device=device)/max(len(chunks)-1,1),
                                current_counts/owner_counts.clamp(min=1),
                                student_counts/owner_counts.clamp(min=1)],dim=1)
        position = self.position(positions)
        def attend(values, key, score, available):
            scores = score(torch.tanh(key(values)+self.query_key(query)[None]+position)).squeeze(-1)
            weights = torch.softmax(scores.masked_fill(~available,-1e9),dim=0)
            weights = weights*available
            weights = weights/weights.sum().clamp(min=1e-12)
            return (weights[:,None]*values).sum(0),weights
        context, ca = attend(features[:,0],self.context_key,self.context_score,owner_counts>0)
        student, sa = attend(features[:,1],self.student_key,self.student_score,student_counts>0)
        logits = []
        for head, pooled in zip(self.heads,(context,student),strict=True):
            combined = torch.cat([query,pooled,query*pooled,torch.abs(query-pooled)])
            logits.append(head(combined).squeeze(-1))
        logits = torch.stack(logits)
        return (logits,{'context':ca,'student':sa}) if return_attention else logits

    def forward(self, chunks, return_attention=False):
        return self.classify(chunks,self.encode_chunks(chunks),return_attention)

    def forward_many(self, bags):
        flat = [chunk for bag in bags for chunk in bag]
        features = self.encode_chunks(flat)
        outputs, start = [], 0
        for bag in bags:
            outputs.append(self.classify(bag,features[start:start+len(bag)]))
            start += len(bag)
        return torch.stack(outputs)


def build_model(config):
    from transformers import AutoConfig, AutoModel
    hf = AutoConfig.from_pretrained(config['model_id'],revision=config['revision'])
    if hf.max_position_embeddings < config['chunk_length']:
        raise ValueError('Chunk exceeds pretrained context length')
    hf.reference_compile = False
    encoder = AutoModel.from_pretrained(config['model_id'],revision=config['revision'],config=hf,
                                        attn_implementation='sdpa')
    encoder.float()
    return DialogueClassifier(encoder,hf.hidden_size,config['pad_id'],config['window_batch'])
