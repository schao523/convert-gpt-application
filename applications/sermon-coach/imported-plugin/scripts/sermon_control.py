import json, sys

def evaluate(x):
    op=x.get('operation')
    if op=='route':
        intent=x.get('intent'); routes={'review':'WF-01','follow-up':'WF-02','revision':'WF-03','study':'WF-04'}
        route=routes.get(intent)
        missing=[]
        if intent=='review' and not x.get('sermon_present'):missing.append('sermon')
        if intent=='revision' and not x.get('revision_present'):missing.append('revision')
        if intent=='study' and not x.get('passage_present'):missing.append('passage')
        return {'route':route,'state':'WAIT' if missing or not route else 'ROUTED','missing':missing}
    if op=='sequence':
        limit={'full':10,'simple':3}.get(x.get('mode'))
        step=x.get('step')
        if not limit or type(step)!=int or not 1<=step<=limit:raise ValueError('invalid step/mode')
        action=x.get('action','wait')
        if action in ['pause','stop']:return {'step':step,'state':action.upper()}
        if action=='revisit':
            target=x.get('target')
            if type(target)!=int or not 1<=target<=step:raise ValueError('invalid revisit')
            return {'step':target,'state':'WAIT'}
        if action=='advance' and x.get('user_confirmed') is True:
            return {'step':min(step+1,limit),'state':'WAIT_COMPLETION_CONFIRMATION' if step==limit else 'WAIT'}
        if action=='complete' and step==limit and x.get('user_confirmed') is True and x.get('all_steps_completed') is True:return {'step':step,'state':'COMPLETE'}
        return {'step':step,'state':'WAIT'}
    if op=='precedence':
        kind=x.get('claim_type')
        return {'authority':{'exact-cuv':'RM-05/RM-06','method':'RM-04-SOURCE','homiletics':'RM-02/RM-03'}.get(kind),'state':'WAIT' if kind not in ['exact-cuv','method','homiletics'] else 'SELECTED'}
    if op=='eligibility':
        kind=x.get('comparison')
        allowed=(x.get('new_present') is True and x.get('prior_present') is True) if kind=='style' else (x.get('revision_present') is True and x.get('before_present') is True) if kind=='revision' else False
        return {'allowed':allowed,'state':'COMPARE' if allowed else 'WAIT_OR_SKIP' if kind=='style' else 'SINGLE_VERSION'}
    raise ValueError('unsupported operation')

if __name__=='__main__':
    request=json.load(sys.stdin)
    if 'cases' in request:result={'results':[evaluate(x) for x in request['cases']]}
    else:result=evaluate(request)
    print(json.dumps(result,ensure_ascii=True,sort_keys=True))
