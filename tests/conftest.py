import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['AROGYA_DB_PATH']=str(ROOT/'data'/'test_knowledge.sqlite3')
from arogyaguard.knowledge import initialize
initialize()
