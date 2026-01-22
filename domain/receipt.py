# coding utf-8
# ᛝ

from dataclasses import dataclass
from typing import List

from domain.cash_register import CashRegister
from domain.payment import Payment
from domain.product import Product
from domain.receipt_meta import ReceiptMeta
from domain.store import Store


@dataclass(slots=True)
class Receipt:
    receipt_meta: ReceiptMeta
    store: Store
    cash_register: CashRegister
    payment: Payment
    products: List[Product]