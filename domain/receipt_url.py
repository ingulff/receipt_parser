# coding utf-8
# ᛝ

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ReceiptUrl:
    url: str
    fiscal_number: str
    fiscal_sign: str
    fiscal_datetime: datetime
    register_number: str
