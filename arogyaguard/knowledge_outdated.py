"""Local, auditable RAG store: curated summaries and separately indexed government PDFs.

No downloaded PDF is bundled or silently substituted. Source excerpts are limited
and can be traced to document ID and real PDF page when the source was ingested.
"""
import hashlib
import os
import shutil
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
import httpx
from pypdf import PdfReader
from .catalog import SOURCES, CATALOG
from .config import settings, ROOT
from .models import Evidence


def connect():
    settings.db_path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(settings.db_path,timeout=20,check_same_thread=False)
    db.row_factory=sqlite3.Row
    return db


def initialize():
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS passages(
          id INTEGER PRIMARY KEY, document_id TEXT NOT NULL, page INTEGER,
          text TEXT NOT NULL, kind TEXT NOT NULL, content_hash TEXT NOT NULL,
          UNIQUE(document_id,page,kind,content_hash))''')
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS passages_fts USING fts5(text, content='passages', content_rowid='id', tokenize='unicode61')")
        db.executescript('''
          CREATE TRIGGER IF NOT EXISTS passage_ai AFTER INSERT ON passages BEGIN INSERT INTO passages_fts(rowid,text) VALUES(new.id,new.text); END;
          CREATE TRIGGER IF NOT EXISTS passage_ad AFTER DELETE ON passages BEGIN INSERT INTO passages_fts(passages_fts,rowid,text) VALUES('delete',old.id,old.text); END;
        ''')
        for doc in SOURCES:
            data=doc['summary']; key=hashlib.sha256(data.encode()).hexdigest()
            db.execute("INSERT OR IGNORE INTO passages(document_id,page,text,kind,content_hash) VALUES(?,?,?,?,?)",
                       (doc['id'], None,data,'curated-summary',key))
        db.commit()


def source_status():
    with connect() as db:
        indexed=dict((r['document_id'],r['n']) for r in db.execute("SELECT document_id,COUNT(*) n FROM passages WHERE kind='indexed-pdf' GROUP BY document_id"))
    return [{**d, 'indexed_chunks':indexed.get(d['id'],0)} for d in SOURCES]


def indexed_count():
    with connect() as db:
        return db.execute("SELECT COUNT(*) FROM passages WHERE kind='indexed-pdf'").fetchone()[0]


def _windows(text: str, size: int=1050, overlap: int=180):
    text=re.sub(r'\s+',' ',text.replace('\x00',' ')).strip()
    at=0
    while at < len(text):
        end=min(at+size,len(text))
        if end < len(text):
            cut=text.rfind(' ',at+int(size*.7),end)
            if cut>at: end=cut
        if end-at>=90:
            yield text[at:end].strip()
        if end >= len(text):break
        at=max(at+1,end-overlap)


def _ocr_scanned_page(pdf_path: Path, page_number: int) -> str:
    """OCR fallback for image-only pages; never silently invents extractable text.

    page_number is 0-based. PyMuPDF renders, Tesseract recognizes; no network API.
    """
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            'Scanned PDF detected. Install OCR support: '
            'pip install -r requirements-ocr.txt; also install Tesseract OCR.'
        ) from exc

    configured = os.getenv('TESSERACT_CMD', '').strip()
    tesseract = configured or shutil.which('tesseract')
    if not tesseract and os.name == 'nt':
        common = Path('C:/Program Files/Tesseract-OCR/tesseract.exe')
        if common.exists():
            tesseract = str(common)
    if not tesseract or not Path(tesseract).is_file():
        raise RuntimeError(
            'Scanned PDF detected, but Tesseract OCR is not installed or not found. '
            'Install Tesseract OCR, restart VS Code, or set TESSERACT_CMD in .env.'
        )
    pytesseract.pytesseract.tesseract_cmd = tesseract
    with fitz.open(str(pdf_path)) as pdf:
        page = pdf.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.1, 2.1), alpha=False, colorspace=fitz.csRGB)
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    try:
        return pytesseract.image_to_string(img, lang='eng', config='--psm 3', timeout=50)
    except pytesseract.TesseractError as exc:
        raise RuntimeError(f'OCR failed on PDF page {page_number+1}: {exc}') from exc
    except RuntimeError as exc:
        raise RuntimeError(f'OCR timeout on PDF page {page_number+1}: {exc}') from exc


def index_local_pdf(doc_id: str, pdf_path: Path):
    if doc_id not in CATALOG or CATALOG[doc_id]['kind'] != 'pdf':
        raise ValueError('Document must be an approved official source')
    reader=PdfReader(str(pdf_path), strict=False)
    if len(reader.pages)>500: raise ValueError('PDF page count exceeds limit')
    rows=[]
    ocr_pages=0
    ocr_issue=None
    # The same document can mix digital text and scanned pages. Preserve real page numbers.
    for p,page in enumerate(reader.pages,1):
        raw=page.extract_text() or ''
        if len(raw.strip()) < 90 and os.getenv('AROGYA_OCR_ENABLED', 'true').lower() == 'true':
            # OCR is needed only when page text is absent / insufficient.
            # Limit expensive rendering for unexpectedly large scanned documents.
            if ocr_pages >= 120:
                raise ValueError('OCR page limit (120) reached; document requires manual review')
            try:
                scanned_text=_ocr_scanned_page(pdf_path, p-1)
            except RuntimeError as exc:
                # An otherwise readable document can have image-only covers or drawings;
                # don't discard valid text on other pages because an optional OCR helper is missing.
                ocr_issue=str(exc)
                scanned_text=''
            if len(scanned_text.strip()) > len(raw.strip()):
                raw=scanned_text
            ocr_pages+=1
        for chunk in _windows(raw):
            rows.append((doc_id,p,chunk,'indexed-pdf',hashlib.sha256(chunk.encode('utf-8')).hexdigest()))
    if not rows:
        if ocr_issue:
            raise ValueError(ocr_issue + '; document was not indexed')
        raise ValueError('No usable PDF text even after OCR; document was not indexed')
    with connect() as db:
        db.execute("DELETE FROM passages WHERE document_id=? AND kind='indexed-pdf'",(doc_id,))
        db.executemany("INSERT OR IGNORE INTO passages(document_id,page,text,kind,content_hash) VALUES(?,?,?,?,?)",rows)
        db.commit()
    return {'id':doc_id,'chunks':len(rows),'pages':len(reader.pages),'ocr_pages_attempted':ocr_pages}


def download_and_index(doc_id: str):
    doc=CATALOG.get(doc_id)
    if not doc or doc['kind']!='pdf':raise ValueError('Unknown approved government PDF')
    output=(ROOT/'data'/'official_pdfs'/f'{doc_id}.pdf')
    output.parent.mkdir(parents=True,exist_ok=True)
    with httpx.Client(timeout=50,follow_redirects=True,trust_env=True) as client:
        with client.stream('GET',doc['url']) as resp:
            resp.raise_for_status()
            host=urlparse(str(resp.url)).hostname or ''
            if not (host=='nhm.gov.in' or host.endswith('.nhm.gov.in')):
                raise ValueError('Redirect left approved government domain')
            n=0
            with output.open('wb') as f:
                for chunk in resp.iter_bytes():
                    n+=len(chunk)
                    if n>28*1024*1024:raise ValueError('PDF exceeds size limit')
                    f.write(chunk)
    with output.open('rb') as f:
        if f.read(5)!=b'%PDF-':
            output.unlink(missing_ok=True)
            raise ValueError('Not a PDF response')
    return index_local_pdf(doc_id,output)


def _terms(query: str):
    words=re.findall(r'[a-zA-Z][a-zA-Z0-9]{2,}',query.lower())
    ignore={'the','and','for','not','with','what','when','where','would','can','does','have','should','about',
      'please','their','need','which','this','from','pregnancy','pregnant','woman','women','india','asha','worker','workers',
      'patient','then','will','are','how','tell','into','maternal','health','more','after'}
    return list(dict.fromkeys(w for w in words if w not in ignore))[:30]


def search(query: str, categories: tuple[str,...], limit: int=5) -> list[Evidence]:
    allowed={d['id'] for d in SOURCES if d['category'] in categories or d['id']=='suman'}
    if not allowed:return []
    terms=_terms(query)
    if not terms:return []
    expr=' OR '.join(f'"{word}"' for word in terms)
    with connect() as db:
        matches=db.execute('''SELECT p.*, bm25(passages_fts) rank FROM passages_fts
              JOIN passages p ON p.id=passages_fts.rowid
              WHERE passages_fts MATCH ? ORDER BY rank LIMIT 100''',(expr,)).fetchall()
    hits=[row for row in matches if row['document_id'] in allowed]
    # Original PDF passages should outrank curated notes *when both really match*.
    hits.sort(key=lambda r: (0 if r['kind']=='indexed-pdf' else 1,float(r['rank'])))
    seen=set(); found=[]
    for row in hits:
        doc_id=row['document_id']; page=row['page']; key=(doc_id,page)
        if key in seen:continue
        seen.add(key)
        doc=CATALOG[doc_id]
        found.append(Evidence(evidence_id=f'P{row["id"]}',document_id=doc_id,title=doc['title'],
         url=doc['url'],page=page,text=row['text'][:1150],provenance=row['kind'],
         scope=doc['scope'],score=round(-float(row['rank']),4)))
        if len(found)>=limit:break
    return found
