"""Regression tests for user-reported in-scope false refusals.

These are controlled model simulations; they do not claim live OpenRouter reliability.
"""
import asyncio
import json
from arogyaguard.engine import AgenticEngine
from arogyaguard.models import AskRequest


class FalseRejectionThenReview:
    def __init__(self, agent_names, query):
        self.agents=agent_names
        self.query=query
        self.calls=[]

    async def json_completion(self,system,user,*,max_tokens=1000):
        self.calls.append((system,user))
        if 'SECOND INDEPENDENT scope adjudicator' in system:
            return {'scope':'in_scope','agents':self.agents,'search_queries':{a:self.query for a in self.agents},
                    'rationale':'Maternal-health programme and service entitlement is in scope.'}
        if 'semantic task orchestrator' in system:
            return {'scope':'out_of_scope','agents':[],'rationale':'Unknown policy name (simulated planner error)'}
        if 'GOVERNANCE AND SYNTHESIS' in system:
            data=json.loads(user)
            ids=list(dict.fromkeys(item for f in data['findings'] for item in f.get('evidence_ids',[])))
            return {'answer': 'Available official-source evidence is shown: '+', '.join(f'[{x}]' for x in ids),
                    'citation_ids':ids,'steps':['Check programme applicability with the supervising NHM official'],
                    'caveats':['Precise amounts or current Telangana eligibility not established by this test'],
                    'status':'answered' if ids else 'insufficient_evidence'}
        data=json.loads(user)
        ids=[e['id'] for e in data['retrieved_evidence']][:2]
        return {'summary':'Show the supported government entitlements and document gaps, not an out-of-scope refusal',
                'evidence_ids':ids,'actions':['Verify details with relevant government health authority'],
                'uncertainties':['Programme specifics may not be in retrieved evidence']}


def test_regression_suman_respectful_maternity():
    fake=FalseRejectionThenReview(['guidance'],'SUMAN respectful dignity maternity care government guidelines')
    result=asyncio.run(AgenticEngine(llm=fake,use_graph=False).run(
        AskRequest(question='What does SUMAN say about respectful maternity care?')))
    assert result.status != 'out_of_scope'
    assert 'guidance' in result.agents_used and 'governance' in result.agents_used
    assert any(t.get('step')=='scope_review' and t['review_result']=='in_scope' for t in result.trace)
    assert any(e.document_id == 'suman' for e in result.evidence)


def test_regression_pmsma_incentive_telangana():
    fake=FalseRejectionThenReview(['followup','benefits'],'Extended PMSMA high risk pregnancy ASHA incentive Telangana first phase rollout')
    result=asyncio.run(AgenticEngine(llm=fake,use_graph=False).run(
        AskRequest(question='Are Extended PMSMA incentives available in Telangana?')))
    assert result.status != 'out_of_scope'
    assert 'followup' in result.agents_used and 'benefits' in result.agents_used
    assert any(e.document_id == 'extended_pmsma' for e in result.evidence)


def test_regression_jssk_amount_and_approval():
    fake=FalseRejectionThenReview(['benefits'],'JSSK free cashless entitlements payment approval transport')
    result=asyncio.run(AgenticEngine(llm=fake,use_graph=False).run(
        AskRequest(question='What is the exact JSSK payment and approval procedure?')))
    assert result.status != 'out_of_scope'
    assert 'benefits' in result.agents_used
    assert any(e.document_id == 'jssk' for e in result.evidence)


def test_out_of_scope_still_rejected_after_review():
    class GenuineOutOfScope(FalseRejectionThenReview):
        async def json_completion(self,system,user,*,max_tokens=1000):
            if 'SECOND INDEPENDENT scope adjudicator' in system:
                self.calls.append((system,user))
                return {'scope':'out_of_scope','agents':[],'rationale':'Sports biography, unrelated to maternal care'}
            return await super().json_completion(system,user,max_tokens=max_tokens)
    fake=GenuineOutOfScope([], 'cricket')
    result=asyncio.run(AgenticEngine(llm=fake,use_graph=False).run(
        AskRequest(question='Who is Virat Kohli?')))
    assert result.status=='out_of_scope'
    assert result.agents_used == []
    assert len(fake.calls)==2
    assert any(t.get('step')=='scope_review' for t in result.trace)
