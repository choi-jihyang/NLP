"""Tokenize all source turns; overlapping context, disjoint ownership for pooling."""


def special_wrapper(tokenizer):
    probe = 'A short tokenizer probe.'
    plain = tokenizer.encode(probe, add_special_tokens=False)
    wrapped = tokenizer(probe, add_special_tokens=True, return_special_tokens_mask=True)
    ids, masks = wrapped['input_ids'], wrapped['special_tokens_mask']
    indexes = [i for i,m in enumerate(masks) if not m]
    if not indexes or indexes != list(range(indexes[0],indexes[-1]+1)):
        raise ValueError('Unsupported noncontiguous special-token template')
    if ids[indexes[0]:indexes[-1]+1] != plain:
        raise ValueError('Special-token template changed input content')
    return ids[:indexes[0]], ids[indexes[-1]+1:]


def make_chunks(source, tokenizer, length=4096, overlap=256):
    if not 16 <= length <= 8192:
        raise ValueError('Chunk length must be between 16 and 8192')
    prefix, suffix = special_wrapper(tokenizer)
    capacity = length-len(prefix)-len(suffix)
    if not 0 <= overlap < capacity:
        raise ValueError('Overlap must be smaller than content capacity')
    tokens, student, current = [], [], []
    turns = [*enumerate(source['history']), (-1, {'role':'student','content':source['message']})]
    for index, turn in turns:
        if turn['role'] not in ('student','assistant') or not isinstance(turn['content'],str):
            raise ValueError('Invalid source role/content')
        marker = f'\n[TURN={index}; ROLE={turn["role"]}; CURRENT={index == -1}]\n'
        meta = tokenizer.encode(marker, add_special_tokens=False, truncation=False, verbose=False)
        text = tokenizer.encode(turn['content'], add_special_tokens=False, truncation=False, verbose=False)
        tokens.extend(meta+text)
        student.extend([0]*len(meta)+[int(turn['role']=='student')]*len(text))
        current.extend([0]*len(meta)+[int(index==-1)]*len(text))
    if not tokens:
        raise ValueError('Empty serialized conversation')
    chunks, start, owned = [], 0, 0
    while start < len(tokens):
        end = min(start+capacity,len(tokens))
        skip = 0 if not chunks else overlap
        own = [0]*skip+[1]*(end-start-skip)
        def mask(values,start=start,end=end,own=own):
            return [0]*len(prefix)+[v*o for v,o in zip(values[start:end],own,strict=True)]+[0]*len(suffix)
        chunks.append({'input_ids':prefix+tokens[start:end]+suffix,
                       'student_mask':mask(student), 'current_mask':mask(current),
                       'owner_mask':[0]*len(prefix)+own+[0]*len(suffix),
                       'start':start,'end':end})
        owned += sum(own)
        if end == len(tokens):
            break
        start = end-overlap
    if owned != len(tokens) or sum(sum(c['current_mask']) for c in chunks) != sum(current):
        raise ValueError('Token coverage or overlap ownership failure')
    return chunks, {'tokens':len(tokens),'single_input_tokens':len(tokens)+len(prefix)+len(suffix),
                    'chunks':len(chunks), 'current_tokens':sum(current),
                    'student_tokens':sum(student),'encoded_tokens':sum(len(c['input_ids']) for c in chunks)}
