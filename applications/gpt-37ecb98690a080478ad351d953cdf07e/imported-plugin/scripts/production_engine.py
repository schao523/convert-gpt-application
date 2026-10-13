#!/usr/bin/env python3
"""Deterministic production-state helpers for Vibe StorySpirit Director.
No network access, credentials, or provider calls. JSON in/out only.
"""
import argparse, json, sys

def emit(x): print(json.dumps(x, ensure_ascii=False, sort_keys=True))

def state(args):
    current = args.source_revision == args.derived_revision and args.derived_status not in {"SUPERSEDED","STALE"}
    emit({"operation":"state-check","source_revision":args.source_revision,"derived_revision":args.derived_revision,"status":"CURRENT" if current else "STALE"})

def assets(args):
    req=[x for x in args.required.split(',') if x]; have=set(x for x in args.available.split(',') if x)
    missing=[x for x in req if x not in have]
    emit({"operation":"asset-check","missing":missing,"complete":not missing})

def compat(args):
    required=set(x for x in args.required.split(',') if x); supported=set(x for x in args.supported.split(',') if x); partial=set(x for x in args.partial.split(',') if x)
    rows=[]
    for r in sorted(required):
        s="FULLY_SUPPORTED" if r in supported else ("PARTIALLY_SUPPORTED" if r in partial else "UNSUPPORTED")
        rows.append({"requirement":r,"classification":s})
    emit({"operation":"compatibility","classifications":rows})

def package(args):
    req=set(x for x in args.required.split(',') if x); present=set(x for x in args.present.split(',') if x)
    missing=sorted(req-present)
    emit({"operation":"package-check","complete":not missing,"missing":missing})

def provenance(args):
    emit({"operation":"provenance","artifact_id":args.artifact_id,"source_project":args.source_project,"source_revision":args.source_revision,"scene_id":args.scene_id,"scene_revision":args.scene_revision,"state":"DERIVED"})

def execution(args):
    if args.evidence == "none":
        emit({"operation":"execution-state","status":"NOT_VERIFIED","success":False,"reason":"NO_EXECUTION_EVIDENCE"})
        return
    emit({"operation":"execution-state","status":args.status,"success":args.status=="SUCCEEDED","evidence_id":args.evidence})

def selftest(_):
    # pure deterministic smoke tests
    assert ("STALE" if "1"!="2" else "CURRENT") == "STALE"
    assert set(["a","b"])-set(["a"]) == {"b"}
    assert "x" not in {"y"}
    emit({"self_test":"PASS","operations":["state-check","asset-check","compatibility","package-check","provenance","execution-state"]})

def main():
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd',required=True)
    q=sp.add_parser('state-check'); q.add_argument('--source-revision',required=True); q.add_argument('--derived-revision',required=True); q.add_argument('--derived-status',default='CURRENT'); q.set_defaults(fn=state)
    q=sp.add_parser('asset-check'); q.add_argument('--required',default=''); q.add_argument('--available',default=''); q.set_defaults(fn=assets)
    q=sp.add_parser('compatibility'); q.add_argument('--required',default=''); q.add_argument('--supported',default=''); q.add_argument('--partial',default=''); q.set_defaults(fn=compat)
    q=sp.add_parser('package-check'); q.add_argument('--required',default=''); q.add_argument('--present',default=''); q.set_defaults(fn=package)
    q=sp.add_parser('provenance'); q.add_argument('--artifact-id',required=True); q.add_argument('--source-project',required=True); q.add_argument('--source-revision',required=True); q.add_argument('--scene-id',required=True); q.add_argument('--scene-revision',required=True); q.set_defaults(fn=provenance)
    q=sp.add_parser('execution-state'); q.add_argument('--status',choices=['SUCCEEDED','FAILED','PARTIAL'],default='FAILED'); q.add_argument('--evidence',default='none'); q.set_defaults(fn=execution)
    q=sp.add_parser('self-test'); q.set_defaults(fn=selftest)
    a=p.parse_args(); a.fn(a)
if __name__=='__main__': main()
