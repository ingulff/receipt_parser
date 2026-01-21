# coding utf-8
# ᛝ

from dataclasses import asdict
from datetime import datetime, timedelta

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
        identity_dict['fiscal_datetime'] = identity.fiscal_datetime.isoformat(sep=' ')
        identity_dict['status'] = ReceiptStatus.PENDING
        
        fields = ','.join(identity_dict.keys())
        placeholders = ','.join(['?'] * len(identity_dict))
        values = tuple(identity_dict.values())
        self._session.session.execute(
            f"""
            INSERT INTO
                receipt_identity(
                    {fields},
                    created_datetime,
                    updated_datetime
                )
            VALUES(
                {placeholders},
                strftime('%Y-%m-%d %H:%M:%f', 'now'),
                strftime('%Y-%m-%d %H:%M:%f', 'now')
            )
            """,
            values
        )

    def created_updated_difference(
            self,
            fiscal_number: str,
            fiscal_sign: str
    ) -> timedelta | None:
        identity = self._session.session.execute(
            """
            SELECT
                created_datetime,
                updated_datetime
            FROM
                receipt_identity
            WHERE
                fiscal_number = ? AND
                fiscal_sign = ?
            """,
            (fiscal_number, fiscal_sign)
        ).fetchone()
        if not identity or not identity['created_datetime'] or not identity['updated_datetime']:
            return None

        created_datetime = datetime.fromisoformat(identity['created_datetime'])
        updated_datetime = datetime.fromisoformat(identity['updated_datetime'])
        return updated_datetime - created_datetime

    def get_by_status(
            self,
            status: ReceiptStatus,
            limit: int,
            after_id: int = 0
    ) -> list[tuple[int, ReceiptIdentity, str | None]]:
        identities = self._session.session.execute(
            """
            SELECT
                url,
                fiscal_number,
                fiscal_sign,
                fiscal_datetime,
                register_number,
                receipt_html,
                id
            FROM
                receipt_identity
            WHERE
                status = ? AND
                id > ?
            ORDER BY
                id
            LIMIT ?
            """,
            (status, after_id, limit)
        ).fetchall()

        return [
            (
                identity['id'],
                ReceiptIdentity(
                    url = identity['url'],
                    fiscal_number = identity['fiscal_number'],
                    fiscal_sign = identity['fiscal_sign'],
                    fiscal_datetime = datetime.fromisoformat(identity['fiscal_datetime']),
                    register_number = identity['register_number']
                ),
                identity['receipt_html']
            )
            for identity in identities
        ]

    def get_ids_by_status(
            self,
            status: ReceiptStatus,
            limit: int,
            after_id: int = 0
    ) -> list[int]:
        identity_ids = self._session.session.execute(
            """
            SELECT
                id
            FROM
                receipt_identity
            WHERE
                status = ? AND
                id > ?
            ORDER BY
                id
            LIMIT ?
            """,
            (status, after_id, limit)
        ).fetchall()
        return [identity['id'] for identity in identity_ids]

    def get_by_ids(
            self,
            identity_ids: list[int],
            status: ReceiptStatus
    ) -> list[tuple[int, ReceiptIdentity, str | None]]:
        if not identity_ids:
            return []

        placeholders = ','.join(['?'] * len(identity_ids))
        identities = self._session.session.execute(
            f"""
            SELECT
                id,
                url,
                fiscal_number,
                fiscal_sign,
                fiscal_datetime,
                register_number,
                receipt_html
            FROM
                receipt_identity
            WHERE
                id IN ({placeholders}) AND
                status = ?
            ORDER BY
                id
            """,
            (*identity_ids, status)
        ).fetchall()
        return [
            (
                identity['id'],
                ReceiptIdentity(
                    url = identity['url'],
                    fiscal_number = identity['fiscal_number'],
                    fiscal_sign = identity['fiscal_sign'],
                    fiscal_datetime = datetime.fromisoformat(identity['fiscal_datetime']),
                    register_number = identity['register_number']
                ),
                identity['receipt_html']
            )
            for identity in identities
        ]

    def update_receipt_html(self, fiscal_number: str, fiscal_sign: str, receipt_html: str) -> None:
        self._session.session.execute(
            """
            UPDATE
                receipt_identity
            SET
                receipt_html = ?,
                updated_datetime = strftime('%Y-%m-%d %H:%M:%f', 'now')
            WHERE
                fiscal_number = ? AND
                fiscal_sign = ?
            """,
            (receipt_html, fiscal_number, fiscal_sign)
        )
    
    def status(self, fiscal_number: str, fiscal_sign: str) -> ReceiptStatus | None:
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
        return ReceiptStatus(identity["status"]) if identity else None

    def count_by_status(self, status: ReceiptStatus) -> int:
        identity_count = self._session.session.execute(
            """
            SELECT
                COUNT(*)
            FROM
                receipt_identity
            WHERE
                status = ?
            """,
            (status,)
        ).fetchone()
        return identity_count[0]

    def update_status(self, fiscal_number: str, fiscal_sign: str, new_status: int):
        self._session.session.execute(
            f"""
            UPDATE
                receipt_identity
            SET
                status = ?,
                updated_datetime = strftime('%Y-%m-%d %H:%M:%f', 'now')
            WHERE
                fiscal_number = ? AND
                fiscal_sign = ?
            """,
            (new_status, fiscal_number, fiscal_sign)
        )

    def id(self, fiscal_number: str, fiscal_sign: str) -> int | None:
        identity = self._session.session.execute(
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
        ).fetchone()
        return identity['id'] if identity else None
