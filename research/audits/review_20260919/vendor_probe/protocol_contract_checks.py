"""Offline method-union and required-field checks, not a general JSON Schema validator."""
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'codex/local'
cases=[
    ('request','initialize',True),('request','thread/start',True),('request','turn/start',True),
    ('request','turn/interrupt',True),('request','turn/cancel',False),
    ('notification','item/started',True),('notification','item/start',False),
    ('notification','item/agentMessage/delta',True),('notification','item/update',False),
    ('notification','item/completed',True),('notification','turn/completed',True),
]
fixtures=[
    {'name':'initialize','kind':'request','expected':True,'message':{'id':1,'method':'initialize','params':{'clientInfo':{'name':'vendor_protocol_audit','version':'2026.09.19'},'capabilities':{'experimentalApi':False}}}},
    {'name':'interrupt_valid_not_sent','kind':'request','expected':True,'message':{'id':2,'method':'turn/interrupt','params':{'threadId':'audit-thread-placeholder','turnId':'audit-turn-placeholder'}}},
    {'name':'interrupt_missing_turn_id','kind':'request','expected':False,'message':{'id':3,'method':'turn/interrupt','params':{'threadId':'audit-thread-placeholder'}}},
    {'name':'invalid_cancel','kind':'request','expected':False,'message':{'id':4,'method':'turn/cancel','params':{'threadId':'audit-thread-placeholder','turnId':'audit-turn-placeholder'}}},
    {'name':'agent_delta_valid_not_received','kind':'notification','expected':True,'message':{'method':'item/agentMessage/delta','params':{'threadId':'audit-thread-placeholder','turnId':'audit-turn-placeholder','itemId':'audit-item-placeholder','delta':'schema fixture only'}}},
    {'name':'invalid_generic_update','kind':'notification','expected':False,'message':{'method':'item/update','params':{'threadId':'audit-thread-placeholder','turnId':'audit-turn-placeholder','itemId':'audit-item-placeholder','delta':'schema fixture only'}}},
]
checks=[]
for mode in ['schema','schema_experimental']:
    roots={kind:json.loads((OUT/mode/file).read_text()) for kind,file in [('request','ClientRequest.json'),('notification','ServerNotification.json')]}
    branches={kind:{b['properties']['method']['enum'][0]:b for b in root['oneOf']} for kind,root in roots.items()}
    for kind,method,expected in cases:
        actual=method in branches[kind]
        checks.append({'mode':mode,'test':'exact_method_union','kind':kind,'method':method,'expected':expected,'actual':actual,'pass':actual==expected})
    for fixture in fixtures:
        msg=fixture['message'];root=roots[fixture['kind']];branch=branches[fixture['kind']].get(msg['method'])
        actual=branch is not None
        if actual:
            actual=all(k in msg for k in branch.get('required',[]))
            ref=branch['properties'].get('params',{}).get('$ref')
            if ref:
                params=root['definitions'][ref.rsplit('/',1)[1]]
                actual=actual and all(k in msg.get('params',{}) for k in params.get('required',[]))
        checks.append({'mode':mode,'test':'method_and_required_fields_only','fixture':fixture['name'],'expected':fixture['expected'],'actual':actual,'pass':actual==fixture['expected']})
source_checks=[]
for snapshot in ['old','stable_0.155.1','new']:
    source=(ROOT/'codex/source'/snapshot/'codex-rs/app-server-protocol/src/protocol/common.rs').read_text()
    for _,method,expected in cases[3:]:
        actual=('"'+method+'"') in source
        source_checks.append({'snapshot':snapshot,'method':method,'expected':expected,'actual':actual,'pass':actual==expected})
result={'scope':'offline method-discriminant and required-field checks; not full JSON Schema conformance, no model execution, fixture events are synthetic','passed':sum(c['pass'] for c in checks+source_checks),'total':len(checks+source_checks),'checks':checks,'source_checks':source_checks}
(OUT/'protocol_test_cases.json').write_text(json.dumps({'cases':cases,'fixtures':fixtures},indent=2)+'\n')
(OUT/'protocol_test_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['scope','passed','total']},indent=2))
assert result['passed']==result['total']
