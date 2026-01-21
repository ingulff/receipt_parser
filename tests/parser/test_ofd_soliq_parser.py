# coding utf-8
# ᛝ

from dataclasses import asdict
from dataclasses import replace

import pytest

from parsing.ofd_soliq_parser import OFDSoliqParser
from tests.utils.utils import get_source_dir, load_json, normalize, get_identity

@pytest.mark.parametrize('receipt_uri, expected_parsed_receipt', 
    [
        ('LG420230638021_5240_20260109143119_430522013780.html', 'expected_LG420230638021.json'),
        ('UZ210317270659_38938_20260110145519_299114273494.html', 'expected_UZ210317270659.json')
    ]
)
def test_ofd_soliq_parser(receipt_uri, expected_parsed_receipt):
    dir_path = get_source_dir(__file__)
    with open(dir_path / receipt_uri, encoding="utf-8") as response:
        receipt_response = response.read()
    
    receipt_identity = get_identity(receipt_uri)

    parser = OFDSoliqParser()
    receipt = normalize(asdict(parser.parse(receipt_response, receipt_identity)))
    expected_json = load_json(dir_path / expected_parsed_receipt)
    
    assert expected_json == receipt


@pytest.mark.parametrize('required_field', ['pic', 'barcode'])
def test_ofd_soliq_parser_rejects_missing_required_product_code(required_field):
    dir_path = get_source_dir(__file__)
    receipt_uri = 'LG420230638021_5240_20260109143119_430522013780.html'
    expected = load_json(dir_path / 'expected_LG420230638021.json')
    product_code = expected['products'][0][required_field]
    with open(dir_path / receipt_uri, encoding='utf-8') as response:
        receipt_html = response.read()
    receipt_html = receipt_html.replace(product_code, '', 1)

    with pytest.raises(ValueError, match='missing required PIC or barcode'):
        OFDSoliqParser().parse(receipt_html, get_identity(receipt_uri))


def test_ofd_soliq_parser_rejects_identity_mismatch():
    dir_path = get_source_dir(__file__)
    receipt_uri = 'LG420230638021_5240_20260109143119_430522013780.html'
    with open(dir_path / receipt_uri, encoding='utf-8') as response:
        receipt_html = response.read()
    identity = replace(get_identity(receipt_uri), fiscal_number='incorrect')

    with pytest.raises(ValueError, match='invalid fiscal number'):
        OFDSoliqParser().parse(receipt_html, identity)

