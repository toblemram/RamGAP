import sys, os, json
sys.path.insert(0, r'c:\Users\TBLM\RamGAP\RamGAP\backend')
from dotenv import load_dotenv
load_dotenv(r'c:\Users\TBLM\RamGAP\RamGAP\.env', override=True)
from activities.plaxis_agent.indexer import get_indexer_status
print(json.dumps(get_indexer_status(), indent=2, default=str))
