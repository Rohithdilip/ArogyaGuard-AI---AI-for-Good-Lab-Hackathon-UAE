"""Safely migrate an existing V2 local index to a newly extracted V3 folder.

Never copies secrets, never overwrites a destination SQLite without --replace.
Use while both application processes are STOPPED.
"""
from pathlib import Path
from shutil import copy2,copytree
from datetime import datetime
from arogyaguard.config import ROOT
import argparse

def main():
    parser=argparse.ArgumentParser(description='Copy the indexed V2 government PDF passages into V3.')
    parser.add_argument('--source',required=True,help='Unzipped V2 project root folder')
    parser.add_argument('--replace',action='store_true',help='Back up and replace existing V3 database')
    args=parser.parse_args()
    src=Path(args.source).resolve()
    old=src/'data'/'knowledge.sqlite3'
    new=ROOT/'data'/'knowledge.sqlite3'
    if not old.is_file():parser.error(f'Cannot find V2 database at: {old}')
    new.parent.mkdir(parents=True,exist_ok=True)
    if new.exists():
        if not args.replace:parser.error('Destination database already exists. To back up and replace, add --replace.')
        backup=new.with_name('knowledge.backup-'+datetime.now().strftime('%Y%m%d%H%M%S')+'.sqlite3')
        copy2(new,backup);print('Backed up existing V3 index:',backup)
    copy2(old,new)
    srcpdf=src/'data'/'official_pdfs';target=ROOT/'data'/'official_pdfs'
    if srcpdf.exists():copytree(srcpdf,target,dirs_exist_ok=True)
    print('Migrated',old,'->',new)
    print('Existing SQLite FTS5 PDF passages are retained. NEXT: python -m scripts.build_vectors')
    print('For security, .env/your OpenRouter API key were NOT copied. Copy .env yourself, and never upload it.')
if __name__=='__main__':main()
