from typing import Literal
from pydantic import BaseModel, Field, field_validator
from .catalog import AGENTS

Language = Literal['en','hi','te','kn']
Agent = Literal['guidance','benefits','followup']

class ChatTurn(BaseModel):
    role: Literal['user','assistant']
    content: str = Field(min_length=1, max_length=1500)

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1800)
    language: Language = 'en'
    state: str = Field(default='Telangana', max_length=50)
    conversation: list[ChatTurn] = Field(default_factory=list, max_length=6)

class ExecutionPlan(BaseModel):
    scope: Literal['in_scope','out_of_scope','clarify']
    agents: list[Agent] = Field(default_factory=list)
    search_queries: dict[str, str] = Field(default_factory=dict)
    rationale: str = Field(default='', max_length=260)
    clarification: str = Field(default='', max_length=260)
    scope_reviewed: bool = False
    initial_scope: str = ''

    @field_validator('agents')
    @classmethod
    def unique_agents(cls, value):
        return list(dict.fromkeys(a for a in value if a in AGENTS))

class Evidence(BaseModel):
    evidence_id: str
    document_id: str
    title: str
    url: str
    page: int | None = None
    text: str
    provenance: Literal['indexed-pdf','curated-summary']
    scope: str
    score: float = 0

class SpecialistFinding(BaseModel):
    agent: Agent
    summary: str = Field(default='', max_length=950)
    actions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    failed: bool = False

class GovernedAnswer(BaseModel):
    answer: str = ''
    steps: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    status: Literal['answered','insufficient_evidence','needs_human_review'] = 'insufficient_evidence'

class AskResponse(BaseModel):
    status: Literal['answered','out_of_scope','clarification','insufficient_evidence','needs_human_review','service_error']
    answer: str
    language: Language
    urgent: bool = False
    urgency_notice: str = ''
    agents_used: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    trace: list[dict] = Field(default_factory=list)
    model: str = ''
    disclaimer: str = 'Research prototype for synthetic cases, not a medical device or government service. Clinical decisions and referrals require human professionals.'
