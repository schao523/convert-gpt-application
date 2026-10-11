import hashlib,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REGISTRY_PATH=ROOT/'data/reference-registry.json'
INDEX_PATH=ROOT/'data/cuv-verse-index.json'
CACHE_PATH=ROOT/'data/source-page-extractions.json'

def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def load_registry():
    d=json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    for rid,row in d['references'].items():
        p=ROOT/row['path']
        if not p.is_file(): raise ValueError(f'required source unavailable: {rid}')
        if _sha(p)!=row['sha256']: raise ValueError(f'source identity mismatch: {rid}')
    return d

def load_cache():
    d=json.loads(CACHE_PATH.read_text(encoding='utf-8'))
    return d

def resolve_rm(reg,rid):
    try: row=reg['references'][rid]
    except KeyError: raise ValueError(f'undeclared reference id: {rid}')
    return row,ROOT/row['path']

def material(reg,rid,page=None,query=None):
    row,path=resolve_rm(reg,rid); digest=row['sha256']
    if path.suffix.lower()=='.pdf':
        cache=load_cache(); src=cache['sources'].get(row['path'])
        if not src or src.get('source_sha256')!=digest: raise ValueError(f'extraction cache identity mismatch: {rid}')
        pages=src['pages']
        if query is not None:
            if not isinstance(query,str) or not query: raise ValueError('query required')
            return {'rm_id':rid,'source':row['path'],'source_sha256':digest,'matches':[i+1 for i,t in enumerate(pages) if query in t],'authority':'original-pdf','verification':'EXTRACTED_TEXT_ONLY'}
        if type(page)!=int or not 1<=page<=len(pages): raise ValueError(f'page out of range: {rid}')
        return {'rm_id':rid,'source':row['path'],'source_sha256':digest,'page':page,'text':pages[page-1],'authority':'original-pdf','verification':'EXTRACTED_TEXT_ONLY'}
    return {'rm_id':rid,'source':row['path'],'source_sha256':digest,'page':None,'text':path.read_text(encoding='utf-8'),'authority':row['kind'],'verification':'SOURCE_TEXT'}

def consult(reg,x):
    required=x.get('required_rm_ids'); requested=x.get('consult_rm_ids',required)
    if not isinstance(required,list) or not all(isinstance(v,str) for v in required): raise ValueError('required_rm_ids must be a list')
    if not isinstance(requested,list) or not all(isinstance(v,str) for v in requested): raise ValueError('consult_rm_ids must be a list')
    materials=[]; consulted=[]; missing=[]
    pages=x.get('pages',{})
    scripture_request=x.get('scripture')
    for rid in requested:
        try:
            if rid in ('RM-05','RM-06') and isinstance(scripture_request,dict):
                sm=scripture(reg,scripture_request)
                if sm.get('rm_id')!=rid: raise ValueError(f'Scripture address resolves to {sm.get("rm_id")}, not {rid}')
                materials.append(sm)
            else:
                materials.append(material(reg,rid,page=pages.get(rid) if isinstance(pages,dict) else None))
            consulted.append(rid)
        except ValueError:
            if rid in required: missing.append(rid)
    for rid in required:
        if rid not in consulted and rid not in missing: missing.append(rid)
    limited=bool(missing)
    state='BLOCKED' if limited and not x.get('allow_limited_review',False) else ('LIMITED' if limited else 'NORMAL')
    record={'workflow':x.get('workflow'),'module':x.get('module'),'required_rm_ids':required,'consulted_rm_ids':consulted,'missing_required_rm_ids':missing,'source_identities':{rid:reg['references'][rid]['sha256'] for rid in consulted},'state':state}
    return {'consultation_record':record,'materials':materials}

def scripture(reg,x):
    idx=json.loads(INDEX_PATH.read_text(encoding='utf-8'))
    # cryptographic binding to current packaged authority
    for rid,s in idx['sources'].items():
        if reg['references'][rid]['sha256']!=s['sha256']: raise ValueError('scripture index source mismatch')
    book=x.get('book'); chapter=x.get('chapter'); start=x.get('verse'); end=x.get('end_verse',start)
    if not isinstance(book,str) or book not in idx['book_aliases']: raise ValueError('unsupported book identifier or alias')
    if type(chapter)!=int or type(start)!=int or type(end)!=int or chapter<1 or start<1 or end<start: raise ValueError('invalid Scripture address')
    abbr=idx['book_aliases'][book]; out=[]
    for v in range(start,end+1):
        key=f'{abbr}.{chapter}.{v}'
        row=idx['verses'].get(key)
        if not row: raise ValueError(f'nonexistent or unavailable Scripture address: {book} {chapter}:{v}')
        out.append({'verse':v,'text':row['text'],'pages':row['pages']})
    rm_id=out and idx['verses'][f'{abbr}.{chapter}.{start}']['rm_id']
    src=reg['references'][rm_id]
    return {'normalized_book_id':abbr,'book_name':idx['verses'][f'{abbr}.{chapter}.{start}']['book_name'],'chapter':chapter,'verse':start,'end_verse':end,'verses':out,'text':' '.join(f'{abbr} {chapter}:{r["verse"]} {r["text"]}' for r in out),'rm_id':rm_id,'source':src['path'],'source_sha256':src['sha256'],'source_locators':sorted({p for r in out for p in r['pages']}),'authority':'packaged-CUV-PDF','verification':'DERIVATIVE_INDEX_BOUND_TO_SOURCE'}

def provenance(reg,x):
    consulted=x.get('consulted_rm_ids',[]); supporting=x.get('supporting_rm_ids',[])
    if not set(supporting)<=set(consulted): raise ValueError('supporting references must be a subset of consulted references')
    return {'finding_id':x.get('finding_id'),'review_dimension':x.get('review_dimension'),'supporting_rm_ids':supporting,'source_identities':{rid:reg['references'][rid]['sha256'] for rid in supporting},'verification':'PROVENANCE_RECORDED'}

def legacy_lookup(reg,x):
    # backwards-compatible source-path access, resolved through canonical registry
    source=x.get('source')
    rid=next((rid for rid,row in reg['references'].items() if row['path']==source),None)
    if not rid: raise ValueError('undeclared source')
    if x.get('operation')=='search': return material(reg,rid,query=x.get('query'))
    result=material(reg,rid,page=x.get('page'))
    if x.get('operation')=='contains':
        q=x.get('query');
        if not isinstance(q,str) or not q: raise ValueError('query required')
        return {'rm_id':rid,'source':result['source'],'page':result.get('page'),'contains':q in result['text']}
    return result

def lookup(x):
    reg=load_registry(); op=x.get('operation')
    if op=='consult': return consult(reg,x)
    if op=='scripture': return scripture(reg,x)
    if op=='provenance': return provenance(reg,x)
    if 'rm_id' in x:
        if op=='search': return material(reg,x['rm_id'],query=x.get('query'))
        return material(reg,x['rm_id'],page=x.get('page'))
    return legacy_lookup(reg,x)

if __name__=='__main__':
    try:
        x=json.load(sys.stdin)
        result={'results':[lookup(c) for c in x['cases']]} if 'cases' in x else lookup(x)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    except (ValueError,KeyError,OSError,UnicodeError,json.JSONDecodeError) as e:
        print(json.dumps({'error':str(e),'state':'BLOCKED'},ensure_ascii=False));sys.exit(2)
