"""Build or refresh local Qdrant vectors from existing trusted SQLite PDF chunks."""
import argparse
import json
from arogyaguard.knowledge import initialize
from arogyaguard.vectors import build_vectors,vector_status

def main():
    parser=argparse.ArgumentParser(description='Build a semantic index from already-indexed NHM PDF passages.')
    parser.add_argument('--id',help='Approved source ID (e.g. jssk); default: all PDF passages')
    args=parser.parse_args()
    initialize()
    print('Starting multilingual E5 embedding generation from SQLite PDF passages...')
    print(json.dumps(build_vectors(args.id),indent=2))
    print('Verification:',json.dumps(vector_status(),indent=2))
if __name__=='__main__':main()
