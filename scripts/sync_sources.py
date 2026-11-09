"""python -m scripts.sync_sources [--id jssk]"""
import argparse
from arogyaguard.catalog import SOURCES
from arogyaguard.knowledge import initialize, download_and_index

def main():
    cli=argparse.ArgumentParser(description='Index approved official NHM PDFs')
    cli.add_argument('--id',default='',help='Only this document id')
    args=cli.parse_args()
    initialize()
    for doc in SOURCES:
        if args.id and doc['id']!=args.id:continue
        print(f'Indexing {doc["id"]} ...',flush=True)
        try:print(download_and_index(doc['id']))
        except Exception as exc:print(f'Unable to index {doc["id"]}: {exc}')

if __name__=='__main__':main()
