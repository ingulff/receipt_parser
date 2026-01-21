# coding utf-8
# ᛝ

from dataclasses import dataclass


@dataclass(slots=True)
class CashRegister:
    serial_number: str
    name: str
