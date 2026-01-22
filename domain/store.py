# coding utf-8
# ᛝ

from dataclasses import dataclass


@dataclass(slots=True)
class Store:
    seller_tin: str
    seller_name: str
    address: str
