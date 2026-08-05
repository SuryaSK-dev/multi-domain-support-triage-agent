import hashlib
import json
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / ".llm_cache"
CACHE_DIR.mkdir(exist_ok=True)

def _cache_key(prefix: str, *parts: str) -> str:
    raw = prefix + "||".join(parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

def cache_get(prefix: str, *parts: str):
    key = _cache_key(prefix, *parts)
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None

def cache_set(prefix: str, *parts: str, value) -> None:
    key = _cache_key(prefix, *parts)
    path = CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps(value), encoding="utf-8")