# coding utf-8
# ᛝ

from dataclasses import asdict
import json

import pytest

from utils import fake_request_receipt, get_source_dir, load_json
from ofd_receipt_service import parse_ticket

@pytest.mark.parametrize('raw_receipt_response, expected_parsed_receipt', 
    [
        ('LG420230638021.html', 'expected_LG420230638021.json'),
        ('UZ210317270659.html', 'expected_UZ210317270659.json')
    ]
)
def test_ofd_soliq_parser(raw_receipt_response, expected_parsed_receipt):
    dir_path = get_source_dir(__file__)
    rerceipt_response = fake_request_receipt(dir_path / raw_receipt_response)
    receipt = parse_ticket(rerceipt_response)
    expected_json = load_json(dir_path / expected_parsed_receipt)
    
    assert expected_json == receipt

