# coding utf-8
# ᛝ

from dataclasses import asdict
import json

import pytest

from network.ofd_fetcher import OFDFetcher
from utils.utils import get_resource_dir, load_json, normalize


@pytest.mark.parametrize('remote_url, local_uri, expected_receipt_identity',
    [
        ('https://remote_receipt_LG420230638021.html', 'LG420230638021_5240_20260109143119_430522013780.html', 'expected_receipt_identity_LG420230638021.json'),
        ('https://remote_receipt_UZ210317270659.html', 'UZ210317270659_38938_20260110145519_299114273494.html', 'expected_receipt_identity_UZ210317270659.json')
    ]
)
def test_ofd_fetcher_parse_url(
    remote_url, 
    local_uri, 
    expected_receipt_identity,
    moc_fecher_parse_url
):
    dir_path = get_resource_dir(__file__)
    
    fetcher = OFDFetcher()
    moc_fecher_parse_url(fetcher, local_uri)
    receipt_identity = normalize(asdict(fetcher.parse_url(remote_url)))
    expected = load_json(dir_path / expected_receipt_identity)
    
    assert expected == receipt_identity
