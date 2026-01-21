# coding utf-8
# ᛝ

from datetime import datetime
from unittest.mock import Mock

from database.constants import ReceiptStatus
from database.repositories.receipt_identity_repository import ReceiptIdentityRepository
from domain import ReceiptIdentity


def test_create_sets_pending_and_database_timestamps():
    session = Mock()
    repository = ReceiptIdentityRepository(session)
    identity = ReceiptIdentity(
        url='https://ofd/receipt',
        fiscal_number='123',
        fiscal_sign='456',
        fiscal_datetime=datetime(2026, 1, 2, 3, 4, 5),
        register_number='789'
    )

    repository.create(identity)

    query, params = session.session.execute.call_args.args
    assert 'created_datetime' in query
    assert 'updated_datetime' in query
    assert 'strftime' in query
    assert params[-1] == ReceiptStatus.PENDING
    assert '2026-01-02 03:04:05' in params


def test_get_ids_by_status_uses_keyset_pagination():
    session = Mock()
    session.session.execute.return_value.fetchall.return_value = [{'id': 4}, {'id': 8}]
    repository = ReceiptIdentityRepository(session)

    result = repository.get_ids_by_status(ReceiptStatus.ERROR, 2, 3)

    assert result == [4, 8]
    query, params = session.session.execute.call_args.args
    assert 'id > ?' in query
    assert 'ORDER BY' in query
    assert params == (ReceiptStatus.ERROR, 3, 2)


def test_update_status_updates_timestamp():
    session = Mock()
    repository = ReceiptIdentityRepository(session)

    repository.update_status('123', '456', ReceiptStatus.PARSED)

    query, params = session.session.execute.call_args.args
    assert 'updated_datetime' in query
    assert params == (ReceiptStatus.PARSED, '123', '456')
