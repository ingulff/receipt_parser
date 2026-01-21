# coding utf-8
# ᛝ

from datetime import datetime
import logging
from unittest.mock import Mock

import pytest

import common.constants as constants
from network.ofd_fetcher import OFDFetcher


def test_parse_url_reads_receipt_identity_fields():
    fetcher = OFDFetcher(logging.getLogger('test_ofd_fetcher'))

    identity = fetcher.parse_url(
        'https://ofd.example/receipt?t=fiscal-1&s=sign-2&c=20260102123456&r=register-3'
    )

    assert identity.fiscal_number == 'fiscal-1'
    assert identity.fiscal_sign == 'sign-2'
    assert identity.fiscal_datetime == datetime(2026, 1, 2, 12, 34, 56)
    assert identity.register_number == 'register-3'


def test_get_receipt_uses_timeout_and_returns_response_text(monkeypatch):
    response = Mock()
    response.text = '<receipt />'
    request = Mock(return_value=response)
    monkeypatch.setattr('network.ofd_fetcher.requests.get', request)
    fetcher = OFDFetcher(logging.getLogger('test_ofd_fetcher'))

    result = fetcher.get_receipt('https://ofd.example/receipt')

    assert result == '<receipt />'
    request.assert_called_once_with(
        'https://ofd.example/receipt',
        timeout=constants.REQUEST_TIMEOUT
    )
    response.raise_for_status.assert_called_once_with()


def test_get_receipt_propagates_http_error(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = RuntimeError('http error')
    monkeypatch.setattr('network.ofd_fetcher.requests.get', Mock(return_value=response))
    fetcher = OFDFetcher(logging.getLogger('test_ofd_fetcher'))

    with pytest.raises(RuntimeError, match='http error'):
        fetcher.get_receipt('https://ofd.example/receipt')
