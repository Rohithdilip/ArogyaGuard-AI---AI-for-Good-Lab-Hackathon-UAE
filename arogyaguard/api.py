"""FastAPI: no manual agent controls, no patient persistence, no automated care actions."""
import asyncio
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import ROOT,settings,has_api_key
from .catalog import LANGUAGES,CATALOG
from .models import AskRequest, AskResponse
from .engine import AgenticEngine
from .knowledge import initialize, source_status, indexed_count, download_and_index
from .vectors import vector_status, build_vectors, VectorSetupError
from . import __version__
from .safety import safety_screen, notice

app=FastAPI(title='ArogyaGuard AI — Team RITAM',version=__version__, description='Maternal-health multi-agent RAG proof of concept. Synthetic use only.')
initialize()
engine=AgenticEngine()

@app.get('/api/status')
def status():
    return {'retrieval':vector_status(),'service':'ArogyaGuard AI','version':__version__,'model_ready':has_api_key(),
            'model':settings.model,'mode':'LLM-first · no keyword fallback',
            'indexed_pdf_chunks':indexed_count(),'languages':LANGUAGES, 'demo_only':True,
            'note':'Model ready indicates key present, not a successful OpenRouter request.'}

@app.get('/api/sources')
def sources():
    vec=vector_status()
    enriched=[{**d,'vector_chunks':vec['vector_documents'].get(d['id'],0)} for d in source_status()]
    return {'sources':enriched,'retrieval':vec,'notice':'Curated summaries are labelled. Sync official PDFs for page-aware RAG.'}


class SafetyRequest(BaseModel):
    question: str = Field(min_length=3,max_length=1800)
    language: str = 'en'

@app.post('/api/safety')
async def safety_early(request:SafetyRequest):
    """Lightweight immediate caution before any external LLM call (not a diagnosis)."""
    flags=safety_screen(request.question)
    return {'urgent':flags['possible_danger'], 'uncertain':flags['uncertain_language'],
            'notice':notice(request.language,flags['possible_danger'],flags['uncertain_language'])}

@app.post('/api/ask',response_model=AskResponse)
async def ask(request:AskRequest):
    if not has_api_key():
        raise HTTPException(status_code=409,detail='Add OPENROUTER_API_KEY to .env and restart. LLM routing is required; no keyword fallback.')
    if re.search(r'[\w.+-]+@[\w.-]+\.[\w.-]+',request.question):
        raise HTTPException(422,'Do not enter real patient emails or identifiable data.')
    if re.search(r'(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{9}(?!\d)',request.question):
        raise HTTPException(422,'Do not enter patient phone numbers.')
    return await engine.run(request)

@app.post('/api/sources/{document_id}/sync')
async def sync(document_id:str):
    if document_id not in CATALOG or CATALOG[document_id]['kind']!='pdf':
        raise HTTPException(400,'Only allow-listed official PDF documents can be indexed.')
    try:
        result=await asyncio.to_thread(download_and_index,document_id)
        # Download succeeds independently of vector embedding; don't call a partly
        # vectorized document fully indexed if model setup fails.
        try:
            if vector_status()['vector_count'] > 0:
                result['semantic']=await asyncio.to_thread(build_vectors,document_id)
        except Exception as exc:
            result['semantic_warning']=str(exc)[:230]
        return result
    except Exception as exc:
        raise HTTPException(502,'Unable to download/index document: '+str(exc)[:180])

@app.post('/api/vectors/build')
async def rebuild_vectors():
    try:
        return await asyncio.to_thread(build_vectors)
    except (VectorSetupError,RuntimeError,ValueError,ImportError) as exc:
        raise HTTPException(422,'Cannot build semantic index: '+str(exc)[:320])

@app.get('/')
def home():return FileResponse(ROOT/'web'/'index.html')

app.mount('/web', StaticFiles(directory=str(ROOT/'web')),name='web')
