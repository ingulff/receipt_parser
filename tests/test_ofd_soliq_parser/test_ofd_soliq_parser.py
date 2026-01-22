# coding utf-8
# ᛝ

from dataclasses import asdict
import json

import pytest

from parsing.ofd_soliq_parser import OFDSoliqParser
from utils.utils import fake_request_receipt, get_source_dir, load_json, normalize

@pytest.mark.parametrize('raw_receipt_response, expected_parsed_receipt', 
    [
        ('LG420230638021.html', 'expected_LG420230638021.json'),
        ('UZ210317270659.html', 'expected_UZ210317270659.json')
    ]
)
def test_ofd_soliq_parser(raw_receipt_response, expected_parsed_receipt):
    dir_path = get_source_dir(__file__)
    rerceipt_response = fake_request_receipt(dir_path / raw_receipt_response)
    parser = OFDSoliqParser()
    receipt = normalize(asdict(parser.parse(rerceipt_response)))
    expected_json = load_json(dir_path / expected_parsed_receipt)
    
    assert expected_json == receipt

