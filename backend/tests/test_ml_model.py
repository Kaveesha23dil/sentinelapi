# Synthetic model checks; no live accuracy implied.
import json
from dataclasses import replace
import numpy as np
import pytest
from sentinelapi.ml.dataset import synthetic, chronological_split
from sentinelapi.ml.model import train, save, load, score, matrix
from sentinelapi.ml.experiment import metrics

@pytest.fixture(scope='module')
def trained():
    w,y,s=synthetic(minutes=366)
    training,heldout=chronological_split(w,w[360].start)
    model,meta=train(training,provenance='synthetic-controlled',n_estimators=30)
    return training,heldout,model,meta


def test_reproducibility_split_and_direction(trained):
    training,heldout,model,meta=trained
    other,m=train(training,provenance='synthetic-controlled',n_estimators=30)
    assert m['version']==meta['version']
    assert max(w.end for w in training)<=min(w.start for w in heldout)
    x=matrix([w.values for w in heldout])
    np.testing.assert_array_equal(model.decision_function(x),other.decision_function(x))
    for w,pred in zip(heldout,model.predict(x),strict=True):
        s=score(model,meta,w)
        assert s['anomaly']==(pred==-1)==(s['decision_score']<0)
    unusual=replace(heldout[0],values=(500,.9,0,20,.1,.9,8))
    assert score(model,meta,unusual)['decision_score']<score(model,meta,heldout[0])['decision_score']
    with pytest.raises(ValueError): score(model,meta,replace(heldout[0],api_id='other'))
    with pytest.raises(ValueError): score(model,meta|{'schema':'bad'},heldout[0])
    with pytest.raises(ValueError): chronological_split(training,training[0].start)


def test_artifact_integrity_and_compatibility(tmp_path,trained):
    _,heldout,model,meta=trained
    saved=save(tmp_path/'model',model,meta)
    restored,m=load(tmp_path/'model',saved['artifact_sha256'])
    assert score(restored,m,heldout[0])==score(model,meta,heldout[0])
    with pytest.raises(ValueError): load(tmp_path/'model','wrong')
    manifest=tmp_path/'model'/'metadata.json'
    manifest.write_text(json.dumps(saved|{'features':['bad']}))
    with pytest.raises(ValueError): load(tmp_path/'model',saved['artifact_sha256'])
    manifest.write_text(json.dumps(saved))
    with (tmp_path/'model'/'model.joblib').open('ab') as f: f.write(b'corrupt')
    with pytest.raises(ValueError): load(tmp_path/'model',saved['artifact_sha256'])


def test_invalid_training_and_features(trained):
    training,_,_,_=trained
    with pytest.raises(ValueError): train(training[:2],provenance='synthetic-controlled')
    with pytest.raises(ValueError): train(training,provenance='unknown')
    with pytest.raises(ValueError): matrix([(5,float('nan'),0,1,1,0,1)])
    with pytest.raises(ValueError): matrix([(5,.9,.9,1,1,0,1)])


def test_missing_classes_metrics():
    normal=metrics([0,0],[0,1])
    assert normal['precision'] is None and normal['recall'] is None and normal['f1'] is None
    assert normal['false_positive_rate']==.5
    assert metrics([1,1],[0,1])['false_positive_rate'] is None
    assert metrics([],[])['windows']==0
