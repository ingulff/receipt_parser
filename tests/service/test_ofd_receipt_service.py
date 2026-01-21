# coding utf-8
# ᛝ

import json
import logging
from datetime import datetime
from threading import Event
from unittest.mock import Mock

import pytest

import common.constants as constants
import ofd_receipt_service as service_module
from database import ReceiptStatus
from domain import ReceiptIdentity
from .fakes import FakeDatabase, FakeFetcher, FakeParser, FakeTransaction


@pytest.fixture
def service_setup(tmp_path, monkeypatch):
    database = FakeDatabase()
    fetcher = FakeFetcher()
    parser = FakeParser()
    logger = Mock(spec=logging.Logger)
    shutdown_event = Event()
    monkeypatch.setattr(service_module, 'Transaction', FakeTransaction)
    service = service_module.Service(
        database_session=database,
        url_lists_path=tmp_path / 'urls',
        parser=parser,
        fetcher=fetcher,
        logger=logger,
        config_path=tmp_path / 'state.json',
        shutdown_event=shutdown_event
    )
    return service, database, fetcher, parser, logger, shutdown_event


def test_url_file_is_processed_in_batches_and_checkpointed(service_setup, tmp_path, monkeypatch):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    url_dir = tmp_path / 'urls'
    url_dir.mkdir()
    urls = ['https://ofd/1', 'https://ofd/2', 'https://ofd/3']
    (url_dir / '20261109_urls.txt').write_text('\n'.join(urls), encoding='utf-8')
    monkeypatch.setattr(constants, 'URL_BATCH_SIZE', 2)
    update_state = service._Service__update_state
    update_state_mock = Mock(wraps=update_state)
    monkeypatch.setattr(service, '_Service__update_state', update_state_mock)

    service.run()

    assert len(database.receipt.receipts) == 3
    assert update_state_mock.call_count == 2
    assert all(record['status'] == ReceiptStatus.PARSED for record in database.receipt_identity.records)
    assert json.loads((tmp_path / 'state.json').read_text(encoding='utf-8')) == {
        'last_file': '20261109_urls.txt',
        'last_url': urls[-1]
    }


def test_checkpoint_resumes_forward_and_ignores_older_files(service_setup, tmp_path):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    url_dir = tmp_path / 'urls'
    url_dir.mkdir()
    older_url = 'https://ofd/older'
    checkpoint_url = 'https://ofd/already-processed'
    next_url = 'https://ofd/next'
    later_file_url = 'https://ofd/later-file'
    (url_dir / '20261107_urls.txt').write_text(older_url, encoding='utf-8')
    (url_dir / '20261108_urls.txt').write_text(
        f'{checkpoint_url}\n{next_url}',
        encoding='utf-8'
    )
    (url_dir / '20261109_urls.txt').write_text(later_file_url, encoding='utf-8')
    checkpoint_identity = fetcher.parse_url(checkpoint_url)
    database.receipt_identity.create(checkpoint_identity)
    database.receipt_identity.update_status(
        checkpoint_identity.fiscal_number,
        checkpoint_identity.fiscal_sign,
        ReceiptStatus.PARSED
    )
    (tmp_path / 'state.json').write_text(json.dumps({
        'last_file': '20261108_urls.txt',
        'last_url': checkpoint_url
    }), encoding='utf-8')

    service.run()

    assert fetcher.fetch_count == {next_url: 1, later_file_url: 1}
    assert [record['identity'].url for record in database.receipt_identity.records] == [
        checkpoint_url,
        next_url,
        later_file_url
    ]


def test_without_url_files_processes_fetched_before_pending(service_setup):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    fetched = fetcher.parse_url('https://ofd/fetched')
    pending = fetcher.parse_url('https://ofd/pending')
    database.receipt_identity.create(fetched)
    database.receipt_identity.update_receipt_html(
        fetched.fiscal_number,
        fetched.fiscal_sign,
        '<cached />'
    )
    database.receipt_identity.update_status(
        fetched.fiscal_number,
        fetched.fiscal_sign,
        ReceiptStatus.FETCHED
    )
    database.receipt_identity.create(pending)

    service.run()

    assert fetcher.fetch_count == {pending.url: 1}
    assert [record['status'] for record in database.receipt_identity.records] == [
        ReceiptStatus.PARSED,
        ReceiptStatus.PARSED
    ]


def test_fetch_error_is_logged_and_service_continues(service_setup, tmp_path):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    url_dir = tmp_path / 'urls'
    url_dir.mkdir()
    bad_url, good_url = 'https://ofd/bad', 'https://ofd/good'
    (url_dir / '20261109_urls.txt').write_text(f'{bad_url}\n{good_url}', encoding='utf-8')
    fetcher.fetch_errors.add(bad_url)

    service.run()

    assert fetcher.fetch_count == {bad_url: 1, good_url: 1}
    statuses = {record['identity'].url: record['status'] for record in database.receipt_identity.records}
    assert statuses == {bad_url: ReceiptStatus.ERROR, good_url: ReceiptStatus.PARSED}
    assert logger.exception.called


def test_parse_error_keeps_fetched_html_for_error_retry(service_setup):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    identity = ReceiptIdentity(
        url='https://ofd/saved',
        fiscal_number='saved',
        fiscal_sign='sign',
        fiscal_datetime=datetime(2026, 1, 1),
        register_number='register'
    )
    database.receipt_identity.create(identity)
    database.receipt_identity.update_receipt_html('saved', 'sign', '<cached />')
    database.receipt_identity.update_status('saved', 'sign', ReceiptStatus.ERROR)
    parser.parse_errors.add('<cached />')

    service._Service__process_identity(identity, '<cached />')

    record = database.receipt_identity.records[0]
    assert record['receipt_html'] == '<cached />'
    assert record['status'] == ReceiptStatus.ERROR
    assert fetcher.fetch_count == {}
    assert logger.exception.called


def test_error_snapshot_is_retried_once_and_does_not_fetch_again(service_setup, monkeypatch):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    identity = ReceiptIdentity(
        url='https://ofd/retry',
        fiscal_number='retry',
        fiscal_sign='sign',
        fiscal_datetime=datetime(2026, 1, 1),
        register_number='register'
    )
    database.receipt_identity.create(identity)
    database.receipt_identity.update_receipt_html('retry', 'sign', '<cached />')
    database.receipt_identity.update_status('retry', 'sign', ReceiptStatus.ERROR)
    parser.parse_errors.add('<cached />')
    monkeypatch.setattr(constants, 'ERROR_RETRY_LIMIT', 1)

    service.run()

    assert parser.parse_count[identity.url] == 1
    assert fetcher.fetch_count == {}
    assert database.receipt_identity.records[0]['status'] == ReceiptStatus.ERROR


def test_graceful_shutdown_finishes_current_url_and_saves_checkpoint(service_setup, tmp_path):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    url_dir = tmp_path / 'urls'
    url_dir.mkdir()
    urls = ['https://ofd/first', 'https://ofd/second']
    (url_dir / '20261109_urls.txt').write_text('\n'.join(urls), encoding='utf-8')
    original_get_receipt = fetcher.get_receipt

    def request_shutdown(url):
        receipt_html = original_get_receipt(url)
        shutdown_event.set()
        return receipt_html

    fetcher.get_receipt = request_shutdown

    service.run()

    assert len(database.receipt.receipts) == 1
    state = json.loads((tmp_path / 'state.json').read_text(encoding='utf-8'))
    assert state['last_url'] == urls[0]


def test_run_logs_database_failure_without_raising(tmp_path, monkeypatch):
    database = Mock()
    logger = Mock(spec=logging.Logger)
    monkeypatch.setattr(service_module, 'Transaction', lambda session: (_ for _ in ()).throw(RuntimeError('database down')))
    service = service_module.Service(
        database_session=database,
        url_lists_path=tmp_path / 'missing_urls',
        parser=FakeParser(),
        fetcher=FakeFetcher(),
        logger=logger,
        config_path=tmp_path / 'state.json'
    )

    service.run()

    assert logger.exception.called


def test_service_does_not_manage_injected_database_lifecycle(service_setup):
    service, database, fetcher, parser, logger, shutdown_event = service_setup
    database.open = Mock()
    database.close = Mock()

    service.run()

    database.open.assert_not_called()
    database.close.assert_not_called()
