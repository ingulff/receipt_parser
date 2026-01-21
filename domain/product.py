# coding utf-8
# ᛝ

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class Product:
    pic: str
    pic_name: str
    barcode: str
    price: Decimal
    quantity: Decimal
    vat_amount: Decimal
    vat_rate: int
    name: str
    unit: str
    discount: str
