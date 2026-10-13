#!/usr/bin/env python3
from pathlib import Path
import json, sys, hashlib
ROOT=Path(__file__).resolve().parents[1]
B=json.loads((ROOT/'docs/reference-bindings.json').read_text(encoding='utf-8'))
CASES=[
 ('RC-01','production-spec-packaging',['RM-P01','RM-P02'],['Package Manifest','machine-readable','not merely']),
 ('RC-02','target-capability-adaptation',['RM-P03'],['TARGET_CAPABILITY_UNVERIFIED','capability evidence','current']),
 ('RC-03','production-execution-review',['RM-P04'],['PREPARED_ONLY','SUBMISSION_EVIDENCED','Execution claims require runtime evidence']),
 ('RC-04','director-orchestrator-state',['RM-P05'],['canonical source state','derived production state','STALE']),
]
results=[]
for tid,skill,rids,anchors in CASES:
    skill_path=ROOT/'skills'/skill/'SKILL.md'
    stxt=skill_path.read_text(encoding='utf-8')
    bound={x['reference_id']:x['path'] for x in B['skills'][skill]}
    missing=[]; blobs=[]; paths=[]
    for rid in rids:
        rel=bound.get(rid)
        if not rel or rel not in stxt:
            missing.append(f'{rid}:binding_not_declared_in_skill')
            continue
        p=ROOT/'skills'/skill/rel
        if not p.is_file():
            missing.append(f'{rid}:file_missing')
            continue
        txt=p.read_text(encoding='utf-8')
        if f'Reference ID:** {rid}' not in txt and f'Reference ID: {rid}' not in txt:
            missing.append(f'{rid}:identity_mismatch')
        blobs.append(txt); paths.append(str(p.relative_to(ROOT)))
    combo='\n'.join(blobs).lower()
    anchor_fail=[a for a in anchors if a.lower() not in combo]
    state='PASS' if not missing and not anchor_fail else 'FAIL'
    results.append({'test_id':tid,'skill':skill,'references':rids,'resolved_paths':paths,'state':state,'missing':missing,'missing_semantic_anchors':anchor_fail})
report={'scope':'PRE_W2_LOCAL_REFERENCE_CONSULTATION_PROBE','installed_runtime_evidence':'NOT VERIFIED','results':results}
out=ROOT/'docs/representative-reference-consultation-results.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if all(r['state']=='PASS' for r in results) else 1)
