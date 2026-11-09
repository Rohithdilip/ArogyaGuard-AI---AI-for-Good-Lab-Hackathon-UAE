"""Offline hybrid integration tests (fake vector search, NOT live Qdrant/model accuracy)."""
import sqlite3
import uuid
from pathlib import Path
from arogyaguard import hybrid, vectors
from arogyaguard.knowledge import connect, initialize
from arogyaguard.config import settings
from fastapi.testclient import TestClient
from arogyaguard.api import app


def _add_pdf(doc='jssk', text='This text describes transport services and eligibility for maternity care.'):
    initialize()
    hash_=str(uuid.uuid4())
    with connect() as db:
        cursor=db.execute("INSERT INTO passages(document_id,page,text,kind,content_hash) VALUES(?,?,?,?,?)",
                       (doc,77,text,'indexed-pdf',hash_))
        pid=cursor.lastrowid
        db.commit()
    return pid


def test_hybrid_retrieves_semantic_only_source(monkeypatch):
    pid=_add_pdf('jssk','A government service provides maternity transport to facilities.')
    monkeypatch.setattr(hybrid,'_lexical_ids',lambda *args,**kwargs:[])
    monkeypatch.setattr(hybrid,'semantic_search',lambda query,allowed,limit=35:[(pid,.93)])
    hits=hybrid.search('completely unrelated vocabulary',('benefits',),limit=4)
    assert hits[0].evidence_id==f'P{pid}'
    assert hits[0].document_id=='jssk'
    assert hits[0].page==77
    assert hits[0].provenance=='indexed-pdf'
    with connect() as db:
        db.execute('DELETE FROM passages WHERE id=?',(pid,));db.commit()


def test_fusion_avoids_duplicate_source_page(monkeypatch):
    pid1=_add_pdf('jssk','JSSK government maternity free transport.')
    pid2=_add_pdf('jssk','JSSK transport for pregnant women.')
    monkeypatch.setattr(hybrid,'_lexical_ids',lambda *args,**kwargs:[pid1,pid2])
    monkeypatch.setattr(hybrid,'semantic_search',lambda query,allowed,limit=35:[(pid2,.95),(pid1,.89)])
    hits=hybrid.search('need hospital transport',('benefits',),limit=5)
    assert sum(h.page==77 for h in hits)==1
    with connect() as db:
        db.execute('DELETE FROM passages WHERE id IN (?,?)',(pid1,pid2));db.commit()


def test_fallback_when_semantic_dependencies_fail(monkeypatch):
    pid=_add_pdf()
    monkeypatch.setattr(hybrid,'_lexical_ids',lambda *args,**kwargs:[pid])
    def fail(*args,**kwargs):raise vectors.VectorSetupError('not installed')
    monkeypatch.setattr(hybrid,'semantic_search',fail)
    hits=hybrid.search('maternal transport',('benefits',))
    assert any(h.evidence_id==f'P{pid}' for h in hits)
    with connect() as db:
        db.execute('DELETE FROM passages WHERE id=?',(pid,));db.commit()


def test_e5_query_and_passage_prefixes(monkeypatch):
    class FakeModel:
        def __init__(self): self.seen=[]
        def encode(self,texts,**kwargs):
            self.seen.extend(texts)
            return [[.1,.5,.3] for _ in texts]
    model=FakeModel()
    monkeypatch.setattr(vectors,'_model',lambda: model)
    assert len(vectors._encode(['Pregnancy transport'],query=True)[0])==3
    assert len(vectors._encode(['JSSK provides transport'],query=False)[0])==3
    assert model.seen==['query: Pregnancy transport','passage: JSSK provides transport']


def test_new_status_exposes_semantic_readiness():
    data=TestClient(app).get('/api/status').json()
    assert data['model']=='openai/gpt-4o-mini' or isinstance(data['model'],str)
    assert data['retrieval']['mode'] in ('hybrid','not_indexed','unavailable','lexical_only')
    assert 'vector_count' in data['retrieval']


def test_source_status_separates_pdf_and_vectors():
    data=TestClient(app).get('/api/sources').json()
    assert data['sources']
    assert all('indexed_chunks' in row and 'vector_chunks' in row for row in data['sources'])


def test_no_fake_vectors_when_qdrant_unavailable(monkeypatch):
    monkeypatch.setattr(vectors,'_client',lambda: (_ for _ in ()).throw(vectors.VectorSetupError('missing qdrant')))
    status=vectors.vector_status()
    assert status['ready'] is False
    assert status['vector_count']==0
    assert status['mode']=='unavailable'
