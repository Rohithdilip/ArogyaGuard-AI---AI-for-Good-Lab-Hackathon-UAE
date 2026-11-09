"""LLM-led, dynamically routed multi-agent RAG. A clinical safety notice is independent.

OpenRouter performs semantic scope and agent decisions. There is no keyword
routing fallback. An optional LangGraph adapter uses Send fan-out; an asyncio
runtime keeps the project testable without the optional graph dependency.
"""
import asyncio
import re
from dataclasses import dataclass
from .catalog import AGENTS, AGENT_LABELS, AGENT_CATEGORIES, LANGUAGES
from .llm import LLMClient, OpenRouterClient, LLMFailure
from .models import AskRequest, AskResponse, ExecutionPlan, SpecialistFinding, GovernedAnswer
from . import prompts
from .hybrid import search
from .vectors import vector_status
from .knowledge import indexed_count
from .safety import safety_screen, notice
from .config import settings


class AgentError(RuntimeError): pass


def compact_history(req: AskRequest):
    return [{'role':x.role,'content':x.content[:900]} for x in req.conversation[-4:]]


def output_language(lang): return LANGUAGES.get(lang,'English')


@dataclass
class AgenticEngine:
    llm: LLMClient | None = None
    use_graph: bool = True

    def __post_init__(self):
        if self.llm is None:self.llm=OpenRouterClient()

    async def plan(self,req:AskRequest)->ExecutionPlan:
        user={'question':req.question,'language':output_language(req.language),
              'region':req.state,'recent_conversation':compact_history(req)}
        import json
        raw=await self.llm.json_completion(prompts.PLANNER,json.dumps(user,ensure_ascii=False),max_tokens=450)
        try:plan=ExecutionPlan.model_validate(raw)
        except Exception as exc:raise AgentError('Orchestrator returned an invalid plan.') from exc
        if plan.scope == 'out_of_scope':
            # Semantic second opinion before rejecting a possible legitimate policy query.
            # Not a keyword allowlist; the reviewer receives the user question and prior context.
            review_context = {**user, 'primary_rationale':plan.rationale}
            raw_review = await self.llm.json_completion(
                prompts.SCOPE_REVIEW, json.dumps(review_context,ensure_ascii=False), max_tokens=600)
            try:
                review=ExecutionPlan.model_validate(raw_review)
            except Exception as exc:
                raise AgentError('Independent scope review returned an invalid plan; the question was not rejected.') from exc
            if review.scope == 'in_scope' and not review.agents:
                # A contradictory plan cannot be safely executed or rejected as unrelated.
                raise AgentError('Scope reviewer considered the question relevant but selected no specialist.')
            # Preserve the review outcome so the execution trace explains a corrected rejection.
            review.scope_reviewed = True
            review.initial_scope = 'out_of_scope'
            return review
        if plan.scope=='in_scope' and not plan.agents:
            # An in-scope question needs at least one specialist.
            raise AgentError('Orchestrator marked the question in scope but selected no agents.')
        return plan

    async def specialist(self, req: AskRequest, plan: ExecutionPlan, agent: str) -> SpecialistFinding:
        if agent not in AGENTS:raise AgentError('Unknown specialist requested')
        query=(plan.search_queries.get(agent) or req.question).strip()[:500]
        # Full user question is available, but evidence retrieval uses LLM-planned semantic query.
        evidence=search(query,AGENT_CATEGORIES[agent],limit=5)
        context={
          'question':req.question,'search_query':query,'state':req.state,
          'preferred_language':output_language(req.language),
          'recent_conversation':compact_history(req),
          'retrieved_evidence':[{'id':e.evidence_id,'source':e.title, 'page':e.page,
                    'scope':e.scope,'provenance':e.provenance,'text':e.text} for e in evidence],
        }
        import json
        if not evidence:
            return SpecialistFinding(agent=agent,summary='The approved knowledge base did not retrieve relevant source passages.',
                uncertainties=['Document retrieval returned no relevant evidence. Index the official PDFs or expand the approved corpus.'],
                evidence=[],failed=True)
        try:
            raw=await self.llm.json_completion(prompts.AGENT_PROMPT.format(agent=AGENT_LABELS[agent]),
                                               json.dumps(context,ensure_ascii=False),max_tokens=750)
            allowed={e.evidence_id for e in evidence}
            ids=list(dict.fromkeys(str(e) for e in raw.get('evidence_ids',[]) if str(e) in allowed))
            # Filter hallucinated evidence references, keep only IDs actually retrieved.
            return SpecialistFinding(agent=agent,
                summary=str(raw.get('summary',''))[:950],
                actions=[str(x)[:320] for x in raw.get('actions',[]) if isinstance(x,str)][:5],
                evidence_ids=ids,
                uncertainties=[str(x)[:250] for x in raw.get('uncertainties',[]) if isinstance(x,str)][:5],
                evidence=[e for e in evidence if e.evidence_id in ids],failed=not bool(ids))
        except (LLMFailure,ValueError,TypeError) as exc:
            return SpecialistFinding(agent=agent,summary='Specialist reasoning was unavailable.',
                  uncertainties=[f'Specialist model failed: {type(exc).__name__}'],evidence=[],failed=True)

    async def govern(self,req:AskRequest,findings:list[SpecialistFinding],safety:dict):
        evidence={e.evidence_id:e for finding in findings for e in finding.evidence}
        import json
        context={
           'question':req.question,'region':req.state,'language':output_language(req.language),
           'safety_notice':notice(req.language,safety['possible_danger'],safety['uncertain_language']),
           'findings':[f.model_dump(exclude={'evidence'}) for f in findings],
           'allowed_evidence':[{'id':e.evidence_id,'source':e.title,'page':e.page,
                                'scope':e.scope,'provenance':e.provenance,'excerpt':e.text[:800]} for e in evidence.values()]
        }
        raw=await self.llm.json_completion(prompts.GOVERNANCE,json.dumps(context,ensure_ascii=False),max_tokens=1000)
        try: draft=GovernedAnswer.model_validate(raw)
        except Exception as exc:raise AgentError('Governance returned malformed results') from exc
        allowed=set(evidence)
        ids=list(dict.fromkeys(x for x in draft.citation_ids if x in allowed))
        answer=draft.answer
        referenced=set(re.findall(r'\[(P\d+)\]',answer))
        invalid=referenced-allowed
        if invalid:
            answer=re.sub(r'\[(P\d+)\]',lambda m: ('['+m.group(1)+']') if m.group(1) in allowed else '',answer)
            draft.caveats.append('Some model-generated citations were not present in retrieved evidence and were removed.')
        if not ids and evidence:
            # If the model neglected to provide the ID list, recover valid in-text IDs only.
            ids=list(referenced.intersection(allowed))
        if not evidence or not ids:
            draft.status='insufficient_evidence'
            answer=('The indexed government evidence is not sufficient for a reliable answer to this question yet. '
                    'Please consult the ASHA/ANM supervisor or qualified facility team. '
                    'Index additional official documents and try again.')
            draft.steps=[]
        if safety['possible_danger']:
            # Safety-first message is always separate from and before unverified AI text.
            draft.status='needs_human_review'
        return draft, answer, [evidence[x] for x in ids]

    def _scope_reply(self,req,plan,safety):
        if plan.scope=='out_of_scope':
            txt={
             'en':'I am ArogyaGuard AI. I can assist ASHA workers with Indian maternal-health guidance, pregnancy referrals, government maternity benefits and follow-up. That question is outside my scope.',
             'hi':'मैं ArogyaGuard AI हूँ। मैं आशा कार्यकर्ताओं को मातृ स्वास्थ्य, गर्भावस्था के रेफरल, सरकारी लाभ और फॉलो-अप में मदद करता हूँ। यह प्रश्न मेरे दायरे से बाहर है।',
             'te':'నేను ArogyaGuard AI. ఆశా కార్యకర్తలకు మాతృ ఆరోగ్యం, రిఫరల్, ప్రభుత్వ పథకాలు మరియు ఫాలో-అప్ గురించి సహాయం చేస్తాను. ఈ ప్రశ్న నా పరిధిలో లేదు.',
             'kn':'ನಾನು ArogyaGuard AI. ಆಶಾ ಕಾರ್ಯಕರ್ತರಿಗೆ ಮಾತೃ ಆರೋಗ್ಯ, ರೆಫರಲ್, ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಮತ್ತು ಫಾಲೋ-ಅಪ್ ಬಗ್ಗೆ ಸಹಾಯ ಮಾಡುತ್ತೇನೆ. ಈ ಪ್ರಶ್ನೆ ನನ್ನ ವ್ಯಾಪ್ತಿಗೆ ಬರುವುದಿಲ್ಲ.'
            }[req.language]
            status='out_of_scope'
        else:
            txt=plan.clarification or 'Could you clarify the maternal-health situation or the government service you are asking about?'
            status='clarification'
        urgent=safety['possible_danger']
        return AskResponse(status=status,answer=txt,language=req.language,
            urgent=urgent,urgency_notice=notice(req.language,urgent,safety['uncertain_language']),
            agents_used=[],trace=([{'step':'scope_review','initial_scope':'out_of_scope','review_result':plan.scope}]
                   if plan.scope_reviewed else [])
                  +[{'step':'intent','outcome':plan.scope,'reason':plan.rationale[:180]}],model=settings.model)

    async def _fallback_execute(self,req:AskRequest,plan:ExecutionPlan,safety:dict):
        findings=await asyncio.gather(*(self.specialist(req,plan,a) for a in plan.agents))
        return list(findings)

    async def _graph_execute(self,req:AskRequest,plan:ExecutionPlan,safety:dict):
        # LangGraph parallel map/reduce: dynamic Send per selected specialist.
        # Not required for minimal Python install; full install includes langgraph.
        try:
            from langgraph.graph import StateGraph, START, END
            from langgraph.types import Send
            from typing import TypedDict, Annotated
            import operator
        except ImportError:
            return await self._fallback_execute(req,plan,safety)
        class State(TypedDict):
            findings: Annotated[list[SpecialistFinding],operator.add]
            selected: list[str]
        class WorkerState(TypedDict):
            agent: str
        async def worker(state:WorkerState):
            finding=await self.specialist(req,plan,state['agent'])
            return {'findings':[finding]}
        def route(state:State):
            return [Send('specialist',{'agent':name}) for name in state['selected']]
        def join(state:State):return {}
        graph=StateGraph(State)
        graph.add_node('specialist',worker)
        graph.add_node('join',join)
        graph.add_conditional_edges(START,route,['specialist'])
        graph.add_edge('specialist','join')
        graph.add_edge('join',END)
        compiled=graph.compile()
        result=await compiled.ainvoke({'findings':[],'selected':plan.agents})
        return result['findings']

    async def run(self,req:AskRequest)->AskResponse:
        safety=safety_screen(req.question)
        try:
            plan=await self.plan(req)
            if plan.scope!='in_scope':return self._scope_reply(req,plan,safety)
            findings=await (self._graph_execute(req,plan,safety) if self.use_graph else self._fallback_execute(req,plan,safety))
            draft,answer,evidence=await self.govern(req,findings,safety)
            trace=([{'step':'scope_review','initial_scope':'out_of_scope','review_result':plan.scope}]
                   if plan.scope_reviewed else []) + [{'step':'intent','outcome':plan.scope,'reason':plan.rationale[:180]},
                {'step':'agent_routing','agents':plan.agents},
                {'step':'retrieval','mode':vector_status()['mode']},
                *[{'step':'specialist','agent':f.agent,'evidence_used':len(f.evidence),
                    'result':'evidence_found' if f.evidence else 'needs_more_evidence'} for f in findings],
                {'step':'governance','result':draft.status,'verified_references':len(evidence)}]
            urgency=safety['possible_danger']
            return AskResponse(status=draft.status,answer=answer,language=req.language,
                urgent=urgency,urgency_notice=notice(req.language,urgency,safety['uncertain_language']),
                agents_used=[f.agent for f in findings]+['governance'], evidence=evidence,
                steps=draft.steps,caveats=draft.caveats,trace=trace,model=settings.model)
        except (LLMFailure,AgentError) as exc:
            msg=str(exc)
            return AskResponse(status='service_error',answer='The AI service could not complete this request: '+msg,
                language=req.language,urgent=safety['possible_danger'],
                urgency_notice=notice(req.language,safety['possible_danger'],safety['uncertain_language']),
                trace=[{'step':'service','outcome':'error','reason':type(exc).__name__}],model=settings.model)
