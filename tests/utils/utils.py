# coding utf-8
# ᛝ

from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path

from domain import ReceiptIdentity


def load_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(content, uri_args):
     with open('resource/in/{}.html'.format(url_args['fiscal_number']), mode='w', encoding='utf-8') as f:
            f.write(response.text)

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


def get_resource_dir(tests_path: str) -> Path:
    return Path(tests_path).parent / 'resource'

def get_identity(uri: str) -> ReceiptIdentity:
    url, ext = uri.split('.')
    fn, rn, fd, fs = map(str, url.split('_'))
    return ReceiptIdentity(
        url = uri,
        fiscal_number = fn,
        fiscal_sign = fs,
        fiscal_datetime = datetime.strptime(fd, "%Y%m%d%H%M%S"),
        register_number = rn
    )