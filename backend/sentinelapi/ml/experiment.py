"""Reproduce controlled synthetic evaluation: python -m sentinelapi.ml.experiment."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from .dataset import synthetic, chronological_split
from .model import train, save, score
from sentinelapi.detection.rules import Observation, configuration, evaluate


def metrics(labels, predictions):
    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel().tolist()
    positive, negative = tp+fn, tn+fp
    precision = tp/(tp+fp) if tp+fp and positive else None
    recall = tp/positive if positive else None
    return dict(confusion_matrix=[[tn, fp], [fn, tp]], precision=precision, recall=recall,
        f1=2*tp/(2*tp+fp+fn) if positive and 2*tp+fp+fn else None,
        false_positive_rate=fp/negative if negative else None,
        windows=len(labels), class_distribution={'normal':negative, 'controlled_scenario':positive})


def run(output, artifacts):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    windows, labels, scenarios, events = synthetic(include_events=True)
    training, heldout = chronological_split(windows, windows[360].start)
    model, metadata = train(training, provenance='synthetic-controlled')
    metadata = save(Path(artifacts)/metadata['version'], model, metadata)
    scored = [score(model, metadata, w) for w in heldout]
    y = labels[360:]
    # Execute the actual Step 6 evaluator on the SAME five-minute histories.
    # Exact same original events, including timestamps and status codes.
    # No client/route-dependent rules are silently enabled.
    rule_predictions = []
    from datetime import timedelta
    from uuid import NAMESPACE_URL, uuid5
    config = configuration('error_rate', {'window_seconds':300, 'threshold':0.5, 'minimum_requests':20})
    observations = [Observation(uuid5(NAMESPACE_URL,e.event_id),e.api_id,e.timestamp,e.status) for e in events]
    for w in heldout:
        history = [o for o in observations if w.end-timedelta(seconds=300)<o.timestamp<=w.end]
        rule_predictions.append(bool(evaluate('error_rate', config, history, w.end)))
    result = dict(provenance='synthetic-controlled', production_ready=False,
        model_version=metadata['version'], evaluation_date=datetime.now(timezone.utc).isoformat(),
        training_windows=len(training), evaluation_windows=len(heldout),
        ml=metrics(y, [s['anomaly'] for s in scored]),
        rules=metrics(y, rule_predictions),
        rule_configuration=config.model_dump(),
        detection_latency_seconds=None,
        latency_note='Offline evaluation; live latency not measured. Finalization waits 120 seconds after window end.',
        comparison_note='Same labeled minutes; Step 6 error-rate uses its actual 300-second history, ML uses 60 seconds.')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output/'evaluation_metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    pd.DataFrame([dict(window_id=w.identifier, start=w.start.isoformat(), label=int(label),
        scenario=scenario, decision_score=s['decision_score'], ml_prediction=int(s['anomaly']),
        rule_prediction=int(rule), **w.summary) for w,label,scenario,s,rule in
        zip(heldout,y,scenarios[360:],scored,rule_predictions,strict=True)]).to_csv(output/'evaluation_windows.csv', index=False)
    fig, ax = plt.subplots(figsize=(6, 5))
    cm = np.asarray(result['ml']['confusion_matrix'])
    ax.imshow(cm, cmap='Blues')
    for (i,j), value in np.ndenumerate(cm):
        ax.text(j,i,str(value),ha='center',va='center')
    ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['Normal','Anomaly'],yticklabels=['Normal','Scenario'],
        xlabel='Predicted',ylabel='Controlled label', title='Synthetic controlled evaluation — Isolation Forest')
    fig.tight_layout(); fig.savefig(output/'confusion_matrix.png'); plt.close(fig)
    fig,ax = plt.subplots(figsize=(7,4))
    scores = np.array([s['decision_score'] for s in scored])
    bins = np.linspace(scores.min(), scores.max(), 21)
    for label,name in [(0,'Normal (includes benign bursts)'),(1,'Controlled scenario')]:
        ax.hist(scores[y==label],bins=bins,alpha=.6,label=name)
    ax.axvline(0,color='black',linestyle='--'); ax.legend()
    ax.set(title='Synthetic controlled decision scores',xlabel='Decision score (lower = more unusual)',ylabel='Windows')
    fig.tight_layout(); fig.savefig(output/'anomaly_score_distribution.png'); plt.close(fig)
    fig,ax = plt.subplots(figsize=(7,4))
    names=['precision','recall','f1','false_positive_rate']; x=np.arange(4)
    for i,kind in enumerate(['ml','rules']):
        ax.bar(x+i*.35,[result[kind][k] or 0 for k in names],.35,label=kind)
    ax.set(xticks=x+.175,xticklabels=names,ylim=(0,1),title='Synthetic controlled comparison (lower FPR is better)')
    ax.legend(); fig.tight_layout(); fig.savefig(output/'model_comparison.png'); plt.close(fig)
    (output/'evaluation_summary.md').write_text('# Controlled synthetic experiment\n\n'+
        'No live attack detection or production accuracy is established.\n\n'+
        json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='infrastructure/ml/evaluation')
    parser.add_argument('--artifacts',default='.runtime/ml/artifacts')
    args=parser.parse_args()
    run(args.output,args.artifacts)
