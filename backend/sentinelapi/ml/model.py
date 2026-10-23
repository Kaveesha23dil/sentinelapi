"""Operator-approved local artifacts only. Checksums provide integrity, NOT trust."""
import hashlib
import io
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import FEATURES, SCHEMA, MIN_REQUESTS


def matrix(rows):
    values = pd.DataFrame(rows, columns=FEATURES).to_numpy(dtype=float)
    if len(values) == 0 or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Non-finite, negative or empty features')
    if (values[:, 0] < MIN_REQUESTS).any() or (values[:, [1, 2, 4, 5]] > 1).any():
        raise ValueError('Ineligible feature values')
    if (values[:, 1]+values[:, 2] > 1.000000001).any() or (values[:, 4]+values[:, 5] > 1.000000001).any():
        raise ValueError('Invalid feature ratios')
    return values


def train(windows, *, provenance, n_estimators=200, contamination=0.05, random_state=42):
    if len(windows) < 60 or not all(w.eligible for w in windows):
        raise ValueError('At least 60 eligible training windows required')
    apis = {w.api_id for w in windows}
    if len({w.identifier for w in windows}) != len(windows):
        raise ValueError('Duplicate training window')
    if len(apis) != 1 or provenance not in {'synthetic-controlled', 'wso2-gateway'}:
        raise ValueError('Train one API and declare provenance')
    if not 1 <= n_estimators <= 2000 or not 0 < contamination <= 0.5:
        raise ValueError('Invalid training configuration')
    x = matrix([w.values for w in windows])
    pipeline = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
        IsolationForest(n_estimators=n_estimators, contamination=contamination,
                        random_state=random_state, n_jobs=1))
    pipeline.fit(x)
    config = dict(n_estimators=n_estimators, contamination=contamination, random_state=random_state)
    dataset_digest = hashlib.sha256(x.tobytes()+
        '|'.join(w.identifier for w in windows).encode()).hexdigest()
    digest = hashlib.sha256((dataset_digest+json.dumps(config, sort_keys=True)+
        str(next(iter(apis)))+SCHEMA+sklearn.__version__+provenance).encode()).hexdigest()
    metadata = dict(version='iforest-'+digest[:16], schema=SCHEMA, features=list(FEATURES),
        api_id=next(iter(apis)), provenance=provenance, production_ready=False,
        trained_at=datetime.now(timezone.utc).isoformat(), training_windows=len(x),
        training_start=min(w.start for w in windows).isoformat(),
        training_end=max(w.end for w in windows).isoformat(), dataset_sha256=dataset_digest,
        sklearn=sklearn.__version__, python=platform.python_version(),
        numpy=np.__version__, joblib=joblib.__version__, config=config,
        score_direction='decision_function < 0 is anomalous; lower is more unusual',
        score_calibration=None)
    return pipeline, metadata


def save(directory, model, metadata):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    artifact = directory/'model.joblib'
    joblib.dump({'model':model, 'metadata':metadata}, artifact)
    metadata = metadata | {'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}
    (directory/'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return metadata


def load(directory, approved_sha256):
    """Digest MUST come from trusted deployment configuration, not a request/manifest.

    joblib executes Python during loading. An attacker-controlled artifact remains
    unsafe even with a matching attacker-controlled checksum. Restrict OS writes.
    Read once, verify those exact bytes, then deserialize to avoid file swap races.
    """
    directory = Path(directory)
    metadata = json.loads((directory/'metadata.json').read_text(encoding='utf-8'))
    if (metadata['schema'] != SCHEMA or metadata['features'] != list(FEATURES) or
        metadata['sklearn'] != sklearn.__version__ or metadata['python'] != platform.python_version() or
        metadata['numpy'] != np.__version__ or metadata['joblib'] != joblib.__version__):
        raise ValueError('Incompatible model artifact')
    data = (directory/'model.joblib').read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if not approved_sha256 or digest != approved_sha256 or digest != metadata['artifact_sha256']:
        raise ValueError('Unapproved or damaged model artifact')
    bundle = joblib.load(io.BytesIO(data))
    if bundle['metadata'] != {k:v for k,v in metadata.items() if k != 'artifact_sha256'}:
        raise ValueError('Artifact metadata mismatch')
    return bundle['model'], metadata


def score(model, metadata, window):
    if not window.eligible or window.api_id != metadata['api_id']:
        raise ValueError('Ineligible window or API baseline mismatch')
    if metadata['schema'] != SCHEMA or metadata['features'] != list(FEATURES):
        raise ValueError('Incompatible feature schema')
    raw = float(model.decision_function(matrix([window.values]))[0])
    if not np.isfinite(raw):
        raise ValueError('Non-finite inference score')
    return {'decision_score': raw, 'anomaly': raw < 0, 'model_version': metadata['version'],
            'window_id': window.identifier, 'features': window.summary}
