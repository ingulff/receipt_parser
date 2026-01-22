# coding utf-8
# ᛝ

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class Payment:
    cash_amount: Decimal
    card_amount: Decimal
    card_type: str
    datetime: datetime
