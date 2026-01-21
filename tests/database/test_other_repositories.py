# coding utf-8
# ᛝ

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

from database.repositories.receipt_repository import ReceiptRepository
from database.repositories.seller_store_repository import SellerStoreRepository
from domain import CashRegister, Payment, Receipt, ReceiptMeta, Store


def test_receipt_repository_saves_receipt_and_both_payment_types():
    session = Mock()
    session.session.execute.return_value.lastrowid = 10
    receipt = Receipt(
        receipt_meta=ReceiptMeta('123', '456', datetime(2026, 1, 1), '789', Decimal('10'), Decimal('1')),
        store=Store('tin', 'seller', 'address'),
        cash_register=CashRegister('register', 'POS'),
        payment=Payment(Decimal('4'), Decimal('6'), 'card', datetime(2026, 1, 1)),
        products=[]
    )
    repository = ReceiptRepository(session)

    repository.create(receipt, {
        'receipt_identity_id': 1,
        'seller_id': 2,
        'cash_register_id': 3
    })

    assert session.session.execute.call_count == 3
    payment_calls = session.session.execute.call_args_list[1:]
    assert all('INSERT INTO' in call.args[0] for call in payment_calls)
    assert payment_calls[0].args[1][0] == 10
    assert payment_calls[1].args[0].find('details') >= 0


def test_seller_repository_reuses_existing_seller_and_register():
    session = Mock()
    session.session.execute.return_value.fetchone.side_effect = [
        {'id': 2},
        {'id': 3}
    ]
    repository = SellerStoreRepository(session)

    result = repository.get_or_create(
        Store('tin', 'seller', 'address'),
        CashRegister('register', 'POS')
    )

    assert result == (2, 3)
    assert session.session.execute.call_count == 2
