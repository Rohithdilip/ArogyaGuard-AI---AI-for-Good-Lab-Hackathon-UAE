"""Persistent Qdrant local semantic index for verified PDF passages.

The LLM is NOT used to embed documents. A local multilingual E5 model embeds
English government passages and multilingual user queries. The vector index is
always rebuilt from trusted SQLite passages; no generated answers are indexed.
"""
from __future__ import annotations
import functools
import os
import threading
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from .config import settings
from .knowledge import connect

COLLECTION = 'nhm_official_pdf_e5_v1'
_BATCH = 48
_MUTEX = threading.RLock()

class VectorSetupError(RuntimeError):
    pass

@functools.lru_cache(maxsize=1)
def _client():
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:
        raise VectorSetupError('qdrant-client is missing. Install: pip install -r requirements-hybrid.txt') from exc
    settings.vector_path.mkdir(parents=True, exist_ok=True)
    # Persistent embedded Qdrant; no Docker/server needed for local development.
    return QdrantClient(path=str(settings.vector_path))

@functools.lru_cache(maxsize=1)
def _model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise VectorSetupError('sentence-transformers is missing. Install requirements-hybrid.txt') from exc
    try:
        return SentenceTransformer(settings.embedding_model, device='cpu')
    except Exception as exc:
        raise VectorSetupError('Could not load multilingual embedding model. The first run needs internet to download it. ' + type(exc).__name__) from exc


def _encode(texts: list[str], *, query: bool) -> list[list[float]]:
    """E5 requires different literal prefixes for queries and passages."""
    prefix='query: ' if query else 'passage: '
    model=_model()
    vectors=model.encode([prefix+s for s in texts],batch_size=16,normalize_embeddings=True,show_progress_bar=False)
    return [v.tolist() if hasattr(v,'tolist') else list(v) for v in vectors]


def _ensure_collection(size:int):
    from qdrant_client import models
    client=_client()
    if not client.collection_exists(COLLECTION):
        client.create_collection(collection_name=COLLECTION, vectors_config=models.VectorParams(size=size,distance=models.Distance.COSINE))
    else:
        collection=client.get_collection(COLLECTION)
        configured=collection.config.params.vectors
        existing_size=configured.size if hasattr(configured,'size') else None
        if existing_size and existing_size!=size:
            raise VectorSetupError('Embedding dimensions changed. Back up and rebuild the Qdrant collection using the same model.')
    return client


def _point_id(passage_id:int) -> str:
    return str(uuid5(NAMESPACE_URL, f'arogyaguard:passage:{passage_id}'))


def vector_status() -> dict:
    """Cheap status check. Never downloads/initializes embedding model."""
    info={'mode':'lexical_only','ready':False,'vector_count':0,'vector_documents':{},'embedding_model':settings.embedding_model,'collection':COLLECTION,
          'message':'Install optional hybrid dependencies, then build the semantic index.'}
    if not settings.vector_enabled:
        info['message']='Semantic retrieval disabled by AROGYA_VECTOR_ENABLED.'
        return info
    try:
        client=_client()
        if not client.collection_exists(COLLECTION):
            info['mode']='not_indexed'
            info['message']='Qdrant is available but the semantic index has not been built. Run python -m scripts.build_vectors.'
            return info
        offset=None
        counts={}
        qdrant_passage_ids=set()
        unexpected_models=set()
        while True:
            points,offset=client.scroll(COLLECTION,limit=256,offset=offset,with_payload=True,with_vectors=False)
            for point in points:
                doc=point.payload.get('document_id') if point.payload else None
                if doc:counts[doc]=counts.get(doc,0)+1
                if point.payload and point.payload.get('passage_id') is not None:
                    qdrant_passage_ids.add(int(point.payload['passage_id']))
                if point.payload and point.payload.get('embedding_model') != settings.embedding_model:
                    unexpected_models.add(str(point.payload.get('embedding_model')))
            if offset is None:break
        count=sum(counts.values())
        with connect() as db:
            expected={int(row[0]) for row in db.execute("SELECT id FROM passages WHERE kind='indexed-pdf'")}
        synced=(bool(count) and expected==qdrant_passage_ids and not unexpected_models)
        if synced:
            mode='hybrid'; message='All current PDF passages have matching semantic vectors.'
        elif not count:
            mode='not_indexed';message='Qdrant is empty. Build vectors from indexed PDFs.'
        else:
            mode='needs_rebuild';message='Qdrant and SQLite passages/model differ. Rebuild semantic index to synchronize.'
        info.update(mode=mode,ready=synced,vector_count=count,vector_documents=counts,message=message)
    except Exception as exc:
        info.update(mode='unavailable',message=f'Semantic search unavailable: {type(exc).__name__}: {str(exc)[:130]}')
    return info


def _fetch_pdf_rows(document_id:str|None=None):
    sql="SELECT id,document_id,page,text,content_hash FROM passages WHERE kind='indexed-pdf'"
    params=()
    if document_id:
        sql+=' AND document_id=?'
        params=(document_id,)
    sql+=' ORDER BY id'
    with connect() as db:
        return [dict(row) for row in db.execute(sql,params).fetchall()]


def _delete_old_ids(client, target_doc:str, valid_ids:set[str]):
    """Delete replaced Qdrant points after new points have been inserted."""
    from qdrant_client import models
    flt=models.Filter(must=[models.FieldCondition(key='document_id',match=models.MatchValue(value=target_doc))])
    old=set()
    offset=None
    while True:
        points,offset=client.scroll(COLLECTION,scroll_filter=flt,limit=256,offset=offset,with_payload=False,with_vectors=False)
        old.update(str(p.id) for p in points)
        if offset is None:break
    obsolete=list(old-valid_ids)
    if obsolete:
        client.delete(COLLECTION,points_selector=models.PointIdsList(points=obsolete),wait=True)


def build_vectors(document_id:str|None=None) -> dict:
    """Backfill vectors from EXISTING verified PDF chunks in SQLite.

    Local model is loaded only when actual chunks exist. Interrupted/upstream
    embedding failures preserve existing SQLite passages. Partial Qdrant
    ingestion never changes SQLite provenance or PDF page metadata.
    """
    if not settings.vector_enabled:
        raise VectorSetupError('Set AROGYA_VECTOR_ENABLED=true in .env')
    try:
        from qdrant_client import models
    except ImportError as exc:
        raise VectorSetupError('qdrant-client is missing. Install requirements-hybrid.txt') from exc
    rows=_fetch_pdf_rows(document_id)
    if not rows:
        raise VectorSetupError('No indexed PDF passages found. Index PDFs first in Evidence Library.')
    docs=sorted({r['document_id'] for r in rows})
    total=0
    with _MUTEX:
        vector_size=None
        for doc in docs:
            items=[r for r in rows if r['document_id']==doc]
            valid=set()
            for start in range(0,len(items),_BATCH):
                batch=items[start:start+_BATCH]
                vectors=_encode([r['text'] for r in batch],query=False)
                if not vectors: continue
                if vector_size is None: vector_size=len(vectors[0])
                client=_ensure_collection(vector_size)
                points=[]
                for row,vector in zip(batch,vectors):
                    pid=_point_id(row['id']);valid.add(pid)
                    points.append(models.PointStruct(id=pid,vector=vector,payload={
                        'passage_id':row['id'],'document_id':row['document_id'],'page':row['page'],
                        'kind':'indexed-pdf','content_hash':row['content_hash'],
                        'embedding_model':settings.embedding_model
                    }))
                client.upsert(COLLECTION,points=points,wait=True)
                total+=len(points)
            if vector_size is not None:
                _delete_old_ids(_client(),doc,valid)
    return {'passages_embedded':total,'documents':docs,'collection':COLLECTION,'embedding_model':settings.embedding_model}


def semantic_search(query:str,allowed:set[str],limit:int=35)->list[tuple[int,float]]:
    if not settings.vector_enabled or not allowed:
        return []
    with _MUTEX:
        client=_client()
        if not client.collection_exists(COLLECTION):return []
        from qdrant_client import models
        vector=_encode([query],query=True)[0]
        filt=models.Filter(must=[models.FieldCondition(key='document_id',match=models.MatchAny(any=sorted(allowed)))])
        response=client.query_points(collection_name=COLLECTION,query=vector,query_filter=filt,limit=limit,with_payload=True)
        return [(int(hit.payload['passage_id']),float(hit.score)) for hit in response.points if hit.payload and 'passage_id' in hit.payload]
