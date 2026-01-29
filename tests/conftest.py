# coding utf-8
# ᛝ

import pytest
from pathlib import Path

from utils.utils import get_identity


class FakeResponse200:
    def __init__(self, text: str):
        self.status_code = 200
        self.text = text
        
    def raise_for_status(self):
        pass


@pytest.fixture
def moc_request_get(monkeypatch):
    def _mock(filename: Path):
        file = filename.read_text(encoding="utf-8")

        monkeypatch.setattr(
            "requests.get", 
            lambda *args, **kwargs: FakeResponse200(file)
        )

    return _mock


@pytest.fixture
def moc_fecher_parse_url(monkeypatch):
    def _mock(fetcher, filename: str):
        print(filename)
        def fake_parse_url(url: str):
            return get_identity(filename)
        monkeypatch.setattr(
            fetcher,
            "parse_url",
            fake_parse_url
        )
    
    return _mock
    
    
@pytest.fixture
def moc_fetcher_get_receipt_200(monkeypatch):
    def _mock(fetcher, filename: Path):
        file = filename.read_text(encoding="utf-8")
        
        def get_fake_receipt(*args, **kwargs):
            return FakeResponse200(file)
        
        monkeypatch.setattr(
            fetcher,
            "get_receipt",
            get_fake_receipt
        )
    
    return _mock
