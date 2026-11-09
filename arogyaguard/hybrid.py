"""Hybrid retrieval: FTS5 lexical ranking + Qdrant semantic ranking via RRF.

No artificial embedding fallback. If the vector layer is absent/broken, the
request continues in clearly labelled lexical-only mode, not fake hybrid RAG.
"""
from __future__ import annotations
import logging
from .catalog import SOURCES, CATALOG
from .knowledge import connect, _terms
from .models import Evidence
from .vectors import semantic_search

LOG=logging.getLogger(__name__)


def _lexical_ids(query:str,allowed:set[str],limit=75):
    terms=_terms(query)
    if not terms:return []
    expr=' OR '.join('"'+t+'"' for t in terms)
    with connect() as db:
        hits=db.execute('''SELECT p.id,p.document_id,p.kind,bm25(passages_fts) AS rank
            FROM passages_fts JOIN passages p ON p.id=passages_fts.rowid
            WHERE passages_fts MATCH ? ORDER BY rank LIMIT 200''',(expr,)).fetchall()
    matches=[r for r in hits if r['document_id'] in allowed]
    matches.sort(key=lambda r:(r['kind']!='indexed-pdf',r['rank']))
    return [int(r['id']) for r in matches[:limit]]


def search(query: str,categories:tuple[str,...],limit:int=5) ->list[Evidence]:
    allowed={d['id'] for d in SOURCES if d['category'] in categories or d['id']=='suman'}
    if not allowed:return []
    lex=_lexical_ids(query,allowed)
    semantic=[]
    try:
        semantic=semantic_search(query,allowed)
    except Exception as exc:
        # No silent semantic claim; /api/status exposes 'unavailable' and logger
        LOG.warning('Qdrant semantic retrieval failed; using FTS5 only: %s',exc)
    scores={}
    for rank,pid in enumerate(lex):scores[pid]=scores.get(pid,0.0)+1/(60+rank+1)
    for rank,(pid,_) in enumerate(semantic):scores[pid]=scores.get(pid,0.0)+1/(60+rank+1)
    if not scores:return []
    keys=list(scores)
    with connect() as db:
        placeholders=','.join('?' for _ in keys)
        result=db.execute(f'SELECT * FROM passages WHERE id IN ({placeholders})',keys).fetchall()
    rows={int(r['id']):r for r in result}
    ranked=sorted((pid for pid in keys if pid in rows and rows[pid]['document_id'] in allowed),
                  key=lambda pid:(-scores[pid],rows[pid]['kind']!='indexed-pdf'))
    seen=set(); evidence=[]
    for pid in ranked:
        row=rows[pid]
        key=(row['document_id'],row['page'])
        if key in seen:continue
        seen.add(key)
        doc=CATALOG[row['document_id']]
        evidence.append(Evidence(evidence_id=f'P{pid}',document_id=doc['id'],title=doc['title'],url=doc['url'],
            page=row['page'],text=row['text'][:1150],provenance=row['kind'],scope=doc['scope'],score=round(scores[pid],5)))
        if len(evidence)>=limit:break
    return evidence
