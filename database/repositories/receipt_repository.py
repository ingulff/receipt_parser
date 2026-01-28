# coding utf-8
# ᛝ

from database.constants import PaymentType 
from database.session import DatabaseSession
from domain import Payment, Product, Receipt

class ReceiptRepository:
    def __init__(self, session: DatabaseSession):
        self._session = session

    def create(self, receipt: Receipt, seller_store_ids):
        receipt_meta_cursor = self._session.session.execute(
            f"""
            INSERT INTO
                receipt_meta(
                    receipt_identity_id,
                    seller_id,
                    cash_register_id,
                    total_amount,
                    total_vat,
                    update_datetime
                )
            VALUES(
                ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
            """,
            (
                seller_store_ids['receipt_identity_id'],
                seller_store_ids['seller_id'],
                seller_store_ids['cash_register_id'],
                float(receipt.receipt_meta.total_amount),
                float(receipt.receipt_meta.total_vat),
            )
        )

        for product in receipt.products:
            product_id = self._create_product(product)
            self._create_receipt_item(
                product, 
                receipt_meta_cursor.lastrowid,
                product_id)

        self._create_receipt_payment(receipt.payment, receipt_meta_cursor.lastrowid)


    def _create_product(self, product: Product) -> int:
        product_cursor = self._session.session.execute(
            f"""
            INSERT INTO
                product(
                    pic,
                    pic_name,
                    barcode,
                    name
                )
            VALUES(
                ?, ?, ?, ?
            )
            """,
            (
                product.pic,
                product.pic_name,
                product.barcode,
                product.name
            )
        )
        return product_cursor.lastrowid

    def _create_receipt_item(self, product: Product, meta_id:int, product_id:int):
        self._session.session.execute(
            f"""
            INSERT INTO
                receipt_item(
                    receipt_meta_id,
                    product_id,
                    price,
                    quantity,
                    vat_amount,
                    vat_rate,
                    unit,
                    discount
                )
            VALUES(
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                meta_id, 
                product_id,
                product.price,
                product.quantity,
                product.vat_amount,
                product.vat_rate,
                product.unit,
                product.discount
            )
        )

    def _create_receipt_payment(self, payment: Payment, meta_id: int):
        payment_dict = {
            'receipt_meta_id': meta_id,
            'currency': "So'm",
            'paid_datetime': payment.datetime
        }

        if payment.cash_amount > 0:
            payment_dict['payment_type_id'] = PaymentType.CASH
            payment_dict['amount'] = payment.cash_amount
            fileds = ','.join(payment_dict.keys())
            placeholders = ','.join(['?'] * len(payment_dict))
            values = tuple(payment_dict.values)
            self._session.session.execute(
                f"""
                INSERT INTO
                    receipt_payment(
                        {fileds}
                    )
                VALUES(
                    {placeholders}
                )
                """,
                values
            )
        
        if payment.card_amount > 0:
            payment_dict['payment_type_id'] = PaymentType.CARD
            payment_dict['amount'] = float(payment.card_amount)
            payment_dict['details'] = payment.card_type
            fileds = ','.join(payment_dict.keys())
            placeholders = ','.join(['?'] * len(payment_dict))
            values = tuple(payment_dict.values())
            self._session.session.execute(
                f"""
                INSERT INTO
                    receipt_payment(
                        {fileds}
                    )
                VALUES(
                    {placeholders}
                )
                """,
                values
            )
