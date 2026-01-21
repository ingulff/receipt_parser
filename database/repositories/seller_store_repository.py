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

    def get_or_create(self, store: Store, cash_register: CashRegister) -> tuple[int, int]:
        seller_id = self.seller_id(store.seller_tin)
        if seller_id is None:
            seller_cursor = self._session.session.execute(
                """
                INSERT INTO seller(tin, name)
                VALUES(?, ?)
                """,
                (store.seller_tin, store.seller_name)
            )
            seller_id = seller_cursor.lastrowid

        cash_register_id = self.cash_register_id(cash_register.serial_number)
        if cash_register_id is not None:
            return seller_id, cash_register_id

        store_row = self._session.session.execute(
            """
            SELECT
                id
            FROM
                store
            WHERE
                seller_id = ? AND
                address = ?
            """,
            (seller_id, store.address)
        ).fetchone()
        if store_row:
            store_id = store_row['id']
        else:
            store_cursor = self._session.session.execute(
                """
                INSERT INTO store(seller_id, address)
                VALUES(?, ?)
                """,
                (seller_id, store.address)
            )
            store_id = store_cursor.lastrowid

        register_cursor = self._session.session.execute(
            """
            INSERT INTO cash_register(serial_number, name, store_id)
            VALUES(?, ?, ?)
            """,
            (cash_register.serial_number, cash_register.name, store_id)
        )
        return seller_id, register_cursor.lastrowid

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
