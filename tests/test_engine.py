import asyncio
import pytest
from arogyaguard.engine import AgenticEngine
from arogyaguard.models import AskRequest
from arogyaguard.knowledge import search, initialize
from arogyaguard.safety import safety_screen

class ScriptedLLM:
    def __init__(self, plan):
        self.plan=plan; self.calls=[]
    async def json_completion(self,system,user,*,max_tokens=1000):
        self.calls.append((system,user))
        if 'semantic' in system.lower() and 'task orchestrator' in system.lower():return self.plan
        if 'SECOND INDEPENDENT scope adjudicator' in system:return self.plan
        if 'GOVERNANCE AND SYNTHESIS' in system:
            import json
            payload=json.loads(user)
            ids=[]
            for x in payload['findings']:ids.extend(x['evidence_ids'])
            ids=list(dict.fromkeys(ids))
            return {'answer':'Use official guidance '+''.join(f'[{x}]' for x in ids), 'steps':['Confirm the appropriate next step with the health facility'],
                    'citation_ids':ids,'caveats':['Local availability must be verified'], 'status':'answered'}
        import json
        content=json.loads(user)
        allowed=[x['id'] for x in content['retrieved_evidence']]
        return {'summary':'Grounded finding from official-source notes', 'actions':['Check the cited source and escalate to qualified staff'],
                 'evidence_ids':allowed[:2], 'uncertainties':[]}

def run_req(plan,question='What free transport does JSSK provide?',language='en'):
    llm=ScriptedLLM(plan)
    response=asyncio.run(AgenticEngine(llm=llm,use_graph=False).run(AskRequest(question=question,language=language)))
    return response,llm

def test_out_of_scope_no_agents_and_no_retrieval():
    res,llm=run_req({'scope':'out_of_scope','agents':[], 'rationale':'Sports question'},question='Who is Virat Kohli?')
    assert res.status=='out_of_scope'
    assert not res.agents_used and not res.evidence
    assert len(llm.calls)==2  # independent semantic review before rejecting
    assert 'Virat' not in res.answer

def test_clarify_does_not_call_agents():
    res,llm=run_req({'scope':'clarify','agents':[], 'clarification':'Which maternal-health question do you need help with?','rationale':'Missing context'},question='What should I do next?')
    assert res.status=='clarification' and len(llm.calls)==1

def test_single_agent_dynamic_routing():
    res,llm=run_req({'scope':'in_scope','agents':['benefits'], 'search_queries':{'benefits':'JSSK free transport maternity entitlement'},'rationale':'Scheme entitlement'})
    assert res.status=='answered'
    assert res.agents_used==['benefits','governance']
    assert len(llm.calls)==3
    assert res.evidence and all(e.document_id in ('jssk','suman') for e in res.evidence)

def test_multiple_agents_genuine_fanout():
    plan={'scope':'in_scope','agents':['guidance','benefits','followup'],
          'search_queries':{'guidance':'danger sign severe headache referral', 'benefits':'JSSK free transport', 'followup':'PMSMA high risk ANC followup'},
          'rationale':'Combined referral transport and follow-up'}
    res,llm=run_req(plan,'Lakshmi has severe headache and blurred vision, missed her ANC appointment and cannot afford transport.')
    assert res.urgent and res.urgency_notice
    assert res.agents_used==['guidance','benefits','followup','governance']
    assert len(llm.calls)==5
    assert all(e.provenance=='curated-summary' for e in res.evidence)
    assert len({e.document_id for e in res.evidence}) >= 2

def test_question_forwarded_to_specialist_llm():
    plan={'scope':'in_scope','agents':['guidance'],'search_queries':{'guidance':'ASHA danger signs pregnancy'},'rationale':'Guidance'}
    original='What should an ASHA worker explain about pregnancy?'
    res,llm=run_req(plan,original)
    assert original in llm.calls[1][1]

def test_language_tough_urgency_backstop():
    assert safety_screen('గర్భిణీకి తీవ్రమైన తలనొప్పి ఉంది')['possible_danger']
    assert safety_screen('गर्भवती को तेज सिरदर्द है')['possible_danger']
    assert safety_screen('ಗರ್ಭಿಣಿಗೆ ತೀವ್ರ ತಲೆನೋವು ಇದೆ')['possible_danger']
    out=safety_screen('No severe headache, only asking about transport')
    assert not out['possible_danger'] and out['uncertain_language']

def test_invalid_citation_removed():
    class Dishonest(ScriptedLLM):
        async def json_completion(self,sys,user,*,max_tokens=1000):
            if 'GOVERNANCE AND SYNTHESIS' in sys:
                return {'answer':'Promise funds [P999999]', 'citation_ids':['P999999'],'status':'answered'}
            return await super().json_completion(sys,user,max_tokens=max_tokens)
    plan={'scope':'in_scope','agents':['benefits'],'search_queries':{'benefits':'JSSK free transport'},'rationale':'Benefit'}
    res=asyncio.run(AgenticEngine(Dishonest(plan),use_graph=False).run(AskRequest(question='Explain JSSK transport')))
    assert res.status=='insufficient_evidence' and 'Promise funds' not in res.answer
    assert not res.evidence

def test_retrieval_is_category_scoped():
    hits=search('free JSSK transport hospital',('benefits',),limit=5)
    assert hits and hits[0].document_id=='jssk'
    assert all(h.document_id in ('jssk','suman') for h in hits)

def test_does_not_retrieve_unrelated_question():
    assert not search('Kohli cricket centuries ODI',('guidance',),limit=5)

def test_unique_agent_plan():
    from arogyaguard.models import ExecutionPlan
    p=ExecutionPlan(scope='in_scope',agents=['benefits','benefits','followup'])
    assert p.agents==['benefits','followup']

def test_negation_not_global():
    assert safety_screen('No transport is available and she has severe headache')['possible_danger']
    assert not safety_screen('She has no severe headache')['possible_danger']
