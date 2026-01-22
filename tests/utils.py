# coding utf-8
# ᛝ

import json
from pathlib import Path


def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_source_dir(tests_path: str) -> Path:
    return Path(tests_path).parent


def fake_request_receipt(path):
    with open(path, mode='r', encoding='utf-8') as f:
        response = f.read()
    
    return response