# coding utf-8
# ᛝ

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path


def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(item):
    if isinstance(item, dict):
        item = {key: normalize(value) for key, value in item.items()}
    
    if isinstance(item, list):
        item = [normalize(value) for value in item]
    
    if isinstance(item, Decimal):
        item = str(item)
    
    if isinstance(item, datetime):
        item = item.strftime("%Y-%m-%d %H:%M:%S")
        
    return item


def get_source_dir(tests_path: str) -> Path:
    return Path(tests_path).parent


def fake_request_receipt(path):
    with open(path, mode='r', encoding='utf-8') as f:
        response = f.read()
    
    return response
