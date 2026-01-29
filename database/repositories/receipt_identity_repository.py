# coding utf-8
# ᛝ

from dataclasses import asdict
from datetime import datetime

from database.constants import ReceiptStatus
from database.session import DatabaseSession
from domain import ReceiptIdentity


class ReceiptIdentityRepository:
    def __init__(self, session: DatabaseSession):
        self._session = session
    
    def exist(self, fiscal_number: str, fiscal_sign: str) -> bool:
        exist_identity = self._session.session.execute(
            """
            SELECT
                id
            FROM 
                receipt_identity
            WHERE
                fiscal_number = ? AND
                fiscal_sign = ?
            """,
            (fiscal_number, fiscal_sign)
        )
        return exist_identity.fetchone() is not None

    def create(self, identity: ReceiptIdentity):
        identity_dict = asdict(identity)
        identity_dict['status'] = ReceiptStatus.FETCHED
        identity_dict['updated_datetime'] = datetime.now().isoformat(sep=' ', timespec='seconds')
        
        fields = ','.join(identity_dict.keys())
        placeholders = ','.join(['?'] * len(identity_dict))
        values = tuple(identity_dict.values())
        self._session.session.execute(
            f"""
            INSERT INTO
                receipt_identity(
                    {fields}
                )
            VALUES(
                {placeholders}
            )
            """,
            values
        )
    
    def status(self, fiscal_number: str, fiscal_sign: str) -> str | None:
        identity = self._session.session.execute(
            f"""
            SELECT
                status
            FROM
                receipt_identity
            WHERE
                fiscal_number = ? AND
                fiscal_sign = ?
            """,
            (fiscal_number, fiscal_sign)
        ).fetchone()
        return identity["status"] if identity else None

    def update_status(self, fiscal_number: str, fiscal_sign: str, new_status: int):
        self._session.session.execute(
            f"""
            UPDATE
                receipt_identity
            SET
                status = ?,
                updated_datetime = CURRENT_TIMESTAMP
            WHERE
                fiscal_number = ? AND
                fiscal_sign = ?
            """,
            (new_status, fiscal_number, fiscal_sign)
        )

    def id(self, fiscal_number: str, fiscal_sign: str) -> int | None:
        identity_cursor = self._session.session.execute(
            f"""
            SELECT
                id
            FROM
                receipt_identity
            WHERE
                fiscal_number = ? AND
                fiscal_sign = ?
            """,
            (fiscal_number, fiscal_sign)
        )
        return identity_cursor.lastrowid if identity_cursor else None
