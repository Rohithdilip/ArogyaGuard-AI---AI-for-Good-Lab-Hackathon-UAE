"""Evaluate ground-truth document recall for lexical and hybrid search.

This does NOT evaluate clinical correctness or answer quality. No fake scores.
Run after indexing government PDFs and building vectors.
"""
from arogyaguard.knowledge import initialize
from arogyaguard.hybrid import search,_lexical_ids
from arogyaguard.catalog import CATALOG
from arogyaguard.knowledge import connect

SAMPLES=[
 ('What maternity transport entitlements are covered by JSSK?',('benefits',),'jssk'),
 ('What should ASHA do for severe headache with blurred vision?',('guidance',),'asha6'),
 ('How can ASHA track a high risk pregnancy after missed ANC visits?',('followup',),'extended_pmsma'),
 ('What respectful maternity care principles are included in SUMAN?',('guidance',),'suman'),
]

def main():
    initialize()
    hits=0
    for query,cats,expected in SAMPLES:
        matches=search(query,cats,limit=5)
        found=any(e.document_id==expected for e in matches)
        hits+=int(found)
        names=', '.join(e.document_id for e in matches)
        print(f'{"PASS" if found else "MISS"} | expected={expected} | retrieved={names}\n  {query}')
    print(f'\nDocument recall@5 in this tiny evaluation set: {hits}/{len(SAMPLES)}. This is not a clinical safety or factuality evaluation.')
if __name__=='__main__':main()
