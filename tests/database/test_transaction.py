# coding utf-8
# ᛝ

from unittest.mock import Mock

import pytest

from database.transaction import Transaction


def test_transaction_commits_on_success():
    session = Mock()

    with Transaction(session):
        pass

    assert [call.args[0] for call in session.session.execute.call_args_list] == ['BEGIN', 'COMMIT']


def test_transaction_rolls_back_on_exception():
    session = Mock()

    with pytest.raises(ValueError):
        with Transaction(session):
            raise ValueError('failed operation')

    assert [call.args[0] for call in session.session.execute.call_args_list] == ['BEGIN', 'ROLLBACK']
