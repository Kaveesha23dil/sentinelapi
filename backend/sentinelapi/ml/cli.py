"""Bounded read-only historical profiling and per-API experimental training."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from uuid import UUID
from sqlalchemy.orm import Session
from sentinelapi.db.session import make_engine
from .dataset import historical, chronological_split
from .features import FEATURES, utc
from .model import train, save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['profile','train'])
    parser.add_argument('--start',type=datetime.fromisoformat,required=True)
    parser.add_argument('--end',type=datetime.fromisoformat,required=True)
    parser.add_argument('--api-id',type=UUID)
    parser.add_argument('--split-at',type=datetime.fromisoformat)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--artifacts',type=Path,default=Path('.runtime/ml/artifacts'))
    parser.add_argument('--n-estimators',type=int,default=200)
    parser.add_argument('--contamination',type=float,default=.05)
    parser.add_argument('--random-state',type=int,default=42)
    args=parser.parse_args()
    if utc(args.start)>=utc(args.end): parser.error('Start must precede end')
    engine=make_engine()
    try:
        with Session(engine) as db:
            windows,profile=historical(db,args.start,args.end,args.api_id)
        import pandas as pd
        frame=pd.DataFrame([w.summary for w in windows if w.eligible],columns=FEATURES)
        profile['distributions']=json.loads(frame.describe().to_json()) if len(frame) else {}
        if args.action=='train':
            if not args.api_id or not args.split_at:
                parser.error('Training requires --api-id and --split-at')
            training,heldout=chronological_split(windows,utc(args.split_at))
            model,metadata=train(training,provenance='wso2-gateway',
                n_estimators=args.n_estimators,contamination=args.contamination,random_state=args.random_state)
            metadata=save(args.artifacts/metadata['version'],model,metadata)
            profile['model']=metadata
            profile['heldout_windows']=len(heldout)
            profile['evaluation']='Unlabeled real traffic; no attack precision/recall claimed'
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(profile,indent=2),encoding='utf-8')
        print('Sanitized historical profile saved; production readiness remains pending.')
    finally:
        engine.dispose()


if __name__=='__main__':
    main()
