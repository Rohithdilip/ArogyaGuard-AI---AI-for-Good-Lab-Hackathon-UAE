from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)

@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv('OPENROUTER_API_KEY', '').strip()
    model: str = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini').strip()
    base_url: str = 'https://openrouter.ai/api/v1/chat/completions'
    db_path: Path = Path(os.getenv('AROGYA_DB_PATH') or str(ROOT / 'data' / 'knowledge.sqlite3'))
    request_timeout: float = float(os.getenv('OPENROUTER_TIMEOUT_SECONDS', '45'))
    vector_enabled: bool = os.getenv('AROGYA_VECTOR_ENABLED','true').strip().lower() in ('true','1','yes')
    vector_path: Path = Path(os.getenv('AROGYA_VECTOR_PATH') or str(ROOT / 'data' / 'qdrant'))
    embedding_model: str = os.getenv('AROGYA_EMBEDDING_MODEL','intfloat/multilingual-e5-small').strip()
    country: str = 'India'
    default_state: str = 'Telangana'
    demo_only: bool = True

settings = Settings()

def has_api_key() -> bool:
    return bool(settings.api_key and not any(x in settings.api_key.upper() for x in ('REPLACE_ME','YOUR_ACTUAL_KEY','PASTE_YOUR_KEY')))

