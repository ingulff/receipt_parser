# coding utf-8
# ᛝ

from database import DatabaseSession
from database.repositories import ReceiptIdentityRepository, ReceiptRepository, SellerStoreRepository

class Repositories:
    def __init__(self, session:DatabaseSession):
        self.seller = SellerStoreRepository(session)
        self.receipt_identity = ReceiptIdentityRepository(session)
        self.receipt = ReceiptRepository(session)

class Transaction:
    def __init__(self, session):
        self.session = session
        self._active = False
        self._repoitory = Repositories(session)

    def __enter__(self):
        self.session.session.execute("BEGIN")
        self.active = True
        return self

    def __exit__(self, exception_type, exception, traseback):
        if exception_type is None:
            self.session.session.execute("COMMIT")
        else:
            self.session.session.execute("ROLLBACK")
        self._active = False

    @property
    def receipt(self):
        return self._repoitory.receipt

    @property
    def receipt_identity(self):
        return self._repoitory.receipt_identity

    @property
    def seller(self):
        return self._repoitory.seller
