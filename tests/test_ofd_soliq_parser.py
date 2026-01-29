# coding utf-8
# ᛝ

from dataclasses import asdict

import pytest

from parsing.ofd_soliq_parser import OFDSoliqParser
from utils.utils import get_resource_dir, load_json, normalize, get_identity


@pytest.mark.parametrize('receipt_uri, expected_parsed_receipt', 
    [
        ('LG420230638021_5240_20260109143119_430522013780.html', 'expected_receipt_LG420230638021.json'),
        ('UZ210317270659_38938_20260110145519_299114273494.html', 'expected_receipt_UZ210317270659.json')
    ]
)
def test_ofd_soliq_parser(receipt_uri, expected_parsed_receipt):
    dir_path = get_resource_dir(__file__)
    
    rerceipt_response = None
    with open(dir_path / receipt_uri) as response:
        rerceipt_response = response.read()
    
    receipt_identity = get_identity(receipt_uri)
    parser = OFDSoliqParser()
    receipt = normalize(asdict(parser.parse(rerceipt_response, receipt_identity)))
    expected = load_json(dir_path / expected_parsed_receipt)
    
    assert expected == receipt

