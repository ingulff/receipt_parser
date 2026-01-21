# coding utf-8
# ᛝ

from datetime import datetime, timedelta
from types import SimpleNamespace

from database import ReceiptStatus
from domain import ReceiptIdentity


class FakeIdentityRepository:
    def __init__(self, records=None):
        self.records = records or []
        self.next_id = max((record['id'] for record in self.records), default=0) + 1

    def exist(self, fiscal_number, fiscal_sign):
        return any(
            record['identity'].fiscal_number == fiscal_number and
            record['identity'].fiscal_sign == fiscal_sign
            for record in self.records
        )

    def create(self, identity):
        self.records.append({
            'id': self.next_id,
            'identity': identity,
            'receipt_html': None,
            'status': ReceiptStatus.PENDING
        })
        self.next_id += 1

    def update_receipt_html(self, fiscal_number, fiscal_sign, receipt_html):
        self._find(fiscal_number, fiscal_sign)['receipt_html'] = receipt_html

    def update_status(self, fiscal_number, fiscal_sign, status):
        self._find(fiscal_number, fiscal_sign)['status'] = ReceiptStatus(status)

    def get_by_status(self, status, limit, after_id=0):
        records = [
            record for record in self.records
            if record['status'] == status and record['id'] > after_id
        ]
        return [
            (record['id'], record['identity'], record['receipt_html'])
            for record in records[:limit]
        ]

    def get_ids_by_status(self, status, limit, after_id=0):
        return [
            record['id'] for record in self.records
            if record['status'] == status and record['id'] > after_id
        ][:limit]

    def get_by_ids(self, identity_ids, status):
        return [
            (record['id'], record['identity'], record['receipt_html'])
            for record in self.records
            if record['id'] in identity_ids and record['status'] == status
        ]

    def created_updated_difference(self, fiscal_number, fiscal_sign):
        return timedelta(seconds=1)

    def id(self, fiscal_number, fiscal_sign):
        return self._find(fiscal_number, fiscal_sign)['id']

    def count_by_status(self, status):
        return sum(record['status'] == status for record in self.records)

    def _find(self, fiscal_number, fiscal_sign):
        for record in self.records:
            identity = record['identity']
            if identity.fiscal_number == fiscal_number and identity.fiscal_sign == fiscal_sign:
                return record
        raise LookupError((fiscal_number, fiscal_sign))


class FakeReceiptRepository:
    def __init__(self):
        self.receipts = []

    def create(self, receipt, ids):
        self.receipts.append((receipt, ids))


class FakeSellerRepository:
    def get_or_create(self, store, cash_register):
        return 1, 1


class FakeDatabase:
    def __init__(self, records=None):
        self.receipt_identity = FakeIdentityRepository(records)
        self.receipt = FakeReceiptRepository()
        self.seller = FakeSellerRepository()


class FakeTransaction:
    def __init__(self, database):
        self.database = database

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        return False

    @property
    def receipt_identity(self):
        return self.database.receipt_identity

    @property
    def receipt(self):
        return self.database.receipt

    @property
    def seller(self):
        return self.database.seller


class FakeFetcher:
    def __init__(self):
        self.fetch_count = {}
        self.html_by_url = {}
        self.fetch_errors = set()

    def parse_url(self, url):
        return ReceiptIdentity(
            url=url,
            fiscal_number=url.rsplit('/', 1)[-1],
            fiscal_sign='sign',
            fiscal_datetime=datetime(2026, 1, 1),
            register_number='register'
        )

    def get_receipt(self, url):
        self.fetch_count[url] = self.fetch_count.get(url, 0) + 1
        if url in self.fetch_errors:
            raise OSError('network error')
        return self.html_by_url.get(url, '<receipt />')


class FakeParser:
    def __init__(self):
        self.parse_errors = set()
        self.parse_count = {}

    def parse(self, receipt_html, identity):
        self.parse_count[identity.url] = self.parse_count.get(identity.url, 0) + 1
        if receipt_html in self.parse_errors:
            raise ValueError('invalid receipt')
        return SimpleNamespace(
            store=SimpleNamespace(seller_tin='tin', seller_name='seller', address='address'),
            cash_register=SimpleNamespace(serial_number='register', name='POS'),
            receipt_meta=SimpleNamespace(total_amount=1, total_vat=0),
            payment=SimpleNamespace(cash_amount=1, card_amount=0, card_type=None, datetime=datetime(2026, 1, 1)),
            products=[]
        )
