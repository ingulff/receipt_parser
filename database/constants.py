# coding utf-8
# ᛝ

from enum import IntEnum

class ReceiptStatus(IntEnum):
    ERROR = 0
    PENDING = 1
    FETCHED = 2
    PARSED = 3

class PaymentType(IntEnum):
    CASH = 1
    CARD = 2
