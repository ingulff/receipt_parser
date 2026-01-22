# coding utf-8
# ᛝ

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class ReceiptMeta:
    fiscal_number: str
    fiscal_sign: str
    fiscal_datetime: datetime
    register_number: str
    total_amount: Decimal
    total_vat: Decimal
