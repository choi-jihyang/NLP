"""Binary-class macro-F1 for each task; thresholds selected on validation only."""

import numpy as np

from .data import LABELS


def binary_metrics(target, prediction):
    target, prediction = np.asarray(target,dtype=bool),np.asarray(prediction,dtype=bool)
    tp,tn = int(np.sum(target&prediction)),int(np.sum(~target&~prediction))
    fp,fn = int(np.sum(~target&prediction)),int(np.sum(target&~prediction))
    def ratio(a,b):
        return a/b if b else 0.
    positive_f1, negative_f1 = ratio(2*tp,2*tp+fp+fn),ratio(2*tn,2*tn+fp+fn)
    return {'macro_f1':(positive_f1+negative_f1)/2,'positive_f1':positive_f1,
            'precision':ratio(tp,tp+fp),'recall':ratio(tp,tp+fn),'fpr':fp/(fp+tn) if fp+tn else None,
            'tp':tp,'tn':tn,'fp':fp,'fn':fn,'positive_support':tp+fn,'negative_support':tn+fp}


def choose_thresholds(target, probabilities):
    target, probabilities = np.asarray(target),np.asarray(probabilities)
    result = []
    for i in range(2):
        options = [(binary_metrics(target[:,i],probabilities[:,i]>=t)['macro_f1'],-abs(t-.5),-t,t)
                   for t in np.linspace(.1,.9,17)]
        result.append(float(max(options)[-1]))
    return result


def evaluate(target, probabilities, thresholds):
    target, probabilities = np.asarray(target),np.asarray(probabilities)
    if target.shape != probabilities.shape or target.ndim!=2 or target.shape[1]!=2 or len(target)==0:
        raise ValueError('Expected nonempty two-label arrays')
    prediction = probabilities>=np.asarray(thresholds)
    labels = {key:binary_metrics(target[:,i],prediction[:,i]) for i,key in enumerate(LABELS)}
    return {'labels':labels,'mean_label_macro_f1':float(np.mean([v['macro_f1'] for v in labels.values()])),
            'exact_match':float(np.mean(np.all(target.astype(bool)==prediction,axis=1))),
            'thresholds':list(thresholds),'rows':len(target),
            'interpretation':'Agreement with automatically verified Qwen labels, not human-gold accuracy.'}
