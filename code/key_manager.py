import os
from dotenv import load_dotenv

load_dotenv()

_keys = [
    os.environ.get("GEMINI_API_KEY_1"),
    os.environ.get("GEMINI_API_KEY_2"),
    os.environ.get("GEMINI_API_KEY_3"),
]
_keys = [k for k in _keys if k]

if not _keys:
    raise RuntimeError("No GEMINI_API_KEY_1/2/3 found in .env")

_current_index = [0]

def get_current_key() -> str:
    return _keys[_current_index[0]]

def rotate_key() -> bool:
    if _current_index[0] + 1 < len(_keys):
        _current_index[0] += 1
        print(f"Switching to API key #{_current_index[0] + 1}/{len(_keys)}")
        return True
    return False

def reset_keys():
    _current_index[0] = 0