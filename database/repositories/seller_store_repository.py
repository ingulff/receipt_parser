# coding utf-8
# ᛝ

from database.session import DatabaseSession
from domain import CashRegister, Store


class SellerStoreRepository:
    def __init__(self, session: DatabaseSession):
        self._session = session

    def create(self, store: Store, cash_register: CashRegister):
        seller_cursor = self._session.session.execute(
            f"""
            INSERT INTO
                seller(
                    tin,
                    name
                )
            VALUES(
                ?, ?
            )
            """,
            (store.seller_tin, store.seller_name)
        )

        store_cursor = self._session.session.execute(
            f"""
            INSERT INTO
                store(
                    seller_id,
                    address
                )
            VALUES(
                ?, ?
            )
            """,
            (seller_cursor.lastrowid, store.address)
        )

        self._session.session.execute(
            f"""
            INSERT INTO
                cash_register(
                    serial_number,
                    name,
                    store_id
                )
            VALUES(
                ?, ?, ?
            )
            """,
            (cash_register.serial_number, cash_register.name, store_cursor.lastrowid)
        )

    def seller_id(self, seller_tin: str) -> int | None:
        seller = self._session.session.execute(
            f"""
            SELECT
                id
            FROM
                seller
            WHERE
                tin = ?
            """,
            (seller_tin,)
        ).fetchone()
        return seller['id'] if seller else None

    def cash_register_id(self, serial_number: str) -> int | None:
        cash_register = self._session.session.execute(
            f"""
            SELECT
                id
            FROM
                cash_register
            WHERE
                serial_number = ?
            """,
            (serial_number,)
        ).fetchone()
        return cash_register['id'] if cash_register else None
