#!/usr/bin/env python3
"""Bounded record validation; no execution of user code or physical-safety certification."""
import json, sys, hashlib
from pathlib import Path

def run(d):
    if not isinstance(d,dict): raise ValueError('input must be an object')
    op=d.get('operation'); checks=[]; limitations=[]
    def check(name,ok): checks.append({'id':name,'pass':bool(ok)})
    if op=='inventory':
        rows=d.get('members',[]); seen=set(); hashes={}
        check('members-present',bool(rows))
        for row in rows:
            name=row.get('path',''); sha=row.get('sha256','')
            check('safe-unique-member:'+name, bool(name) and not Path(name).is_absolute() and '..' not in name.split('/') and name not in seen)
            seen.add(name);check('sha256:'+name,len(sha)==64 and all(c in '0123456789abcdef' for c in sha));hashes.setdefault(sha,[]).append(name)
        for mapping in d.get('mappings',[]):check('mapped-source:'+mapping.get('source',''),mapping.get('source') in seen and bool(mapping.get('target')))
        limitations.append({'duplicate_groups':[v for v in hashes.values() if len(v)>1]})
    elif op=='conversion':
        if not d.get('source_evidence_available'):
            return {'operation':op,'status':'NOT VERIFIED','checks':[],'limitations':['Original source coverage evidence unavailable; no conversion PASS.']}
        for key in ['headings','tables','images','citations']:
            check('coverage:'+key,isinstance(d.get('source_counts',{}).get(key),int) and d['source_counts'][key]==d.get('target_counts',{}).get(key))
        check('exceptions-closed',not d.get('unresolved_exceptions',[]))
        limitations.append('Counts do not establish semantic or visual fidelity; human review remains required.')
    elif op=='activity':
        for key in ['age_or_grade','time','materials','adult_review','measurement','redesign']:check(key,bool(d.get(key)))
        check('focus',bool(d.get('focus')) or d.get('focus_clear') is True)
        check('two-domains',len(set(d.get('steam_domains',[])))>=2)
        check('13-sections',len(d.get('sections',[]))==13)
        check('safety',d.get('safety_review')=='approved' and not d.get('unsafe_hazards',[]))
        check('mode',d.get('mode')=='activity' or d.get('game_switch_confirmed') is True)
        check('state',d.get('state') in ['A6','A7'] and (d.get('state')!='A7' or d.get('adult_review') is True))
    elif op=='production':
        for key in ['approved_design','medium','learning_objective','rules','states','actions','end_conditions','assets','accessibility','inputs_outputs','tests','version']:check(key,bool(d.get(key)))
        check('medium-supported',d.get('medium') in ['printable','web','advanced'])
        check('three-levels',len(d.get('levels',[]))==3)
        states=d.get('states',[]); known={r.get('state') for r in states if isinstance(r,dict)}
        check('state-table',bool(states) and all(isinstance(r,dict) and all(k in r for k in ['state','event','guard','action','next_state']) and r['next_state'] in known for r in states))
        if d.get('produced'):
            check('entrypoint',bool(d.get('entrypoint')))
            content=d.get('artifact_text');check('checksum',isinstance(content,str) and hashlib.sha256(content.encode()).hexdigest()==d.get('artifact_sha256'))
        else:limitations.append('No artifact production asserted; entrypoint execution not verified.')
    elif op=='evidence':
        for claim in ['produced','executed','tested']:
            check(claim+'-evidence',not d.get(claim) or bool(d.get(claim+'_evidence')))
        check('ordered-claims',not d.get('tested') or (d.get('produced') and d.get('executed')))
        check('execution-produced',not d.get('executed') or d.get('produced'))
        check('learning-separate',not d.get('learning_gain_claim') or bool(d.get('learning_observations')))
        limitations.append('Evidence references are supplied records, not independent replay of browser actions.')
    elif op=='usage':
        rows=d.get('rows',[]);check('rows-present',bool(rows))
        for i,r in enumerate(rows):
            for k in ['material_id','trigger','section','provenance','rights_decision']:check(str(i)+':'+k,bool(r.get(k)))
            check(str(i)+':actual-read',r.get('read_state') in ['actual-body-read','unavailable'])
            check(str(i)+':distribution',not r.get('distributed') or r.get('rights_decision')=='owner-approved')
        limitations.append('Owner rights declaration is not an independent license audit.')
    elif op=='framework':
        md=d.get('markdown');other=d.get('comparison_text')
        if not isinstance(md,str) or not isinstance(other,str):return {'operation':op,'status':'NOT VERIFIED','checks':[],'limitations':['Both comparison bodies required; Markdown remains authority.']}
        check('markdown-authority',d.get('authority')=='markdown')
        limitations.append({'bodies_equal':md==other,'markdown_sha256':hashlib.sha256(md.encode()).hexdigest(),'comparison_sha256':hashlib.sha256(other.encode()).hexdigest(),'decision':'Retain Markdown; disclose differences and require review before changes.'})
    else:raise ValueError('unsupported operation')
    return {'operation':op,'status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':checks,'limitations':limitations}

def selftest():
    cases=[({'operation':'evidence','produced':False,'executed':False,'tested':False},'PASS'),({'operation':'evidence','tested':True},'FAIL'),({'operation':'conversion'},'NOT VERIFIED'),({'operation':'framework','markdown':'a','comparison_text':'b','authority':'markdown'},'PASS'),({'operation':'usage','rows':[]},'FAIL'),({'operation':'inventory','members':[{'path':'../x','sha256':'0'*64}]},'FAIL'),({'operation':'activity'},'FAIL'),({'operation':'production'},'FAIL')]
    results=[{'case':i+1,'expected':want,'actual':run(inp)['status']} for i,(inp,want) in enumerate(cases)]
    ok=all(x['expected']==x['actual'] for x in results)
    print(json.dumps({'status':'PASS' if ok else 'FAIL','cases':results},sort_keys=True));return 0 if ok else 1
if __name__=='__main__':
    if sys.argv[1:]==['--self-test']:sys.exit(selftest())
    try:print(json.dumps(run(json.load(sys.stdin)),ensure_ascii=False,sort_keys=True))
    except (ValueError,TypeError,KeyError) as e:print(json.dumps({'status':'ERROR','error':str(e)}));sys.exit(2)
