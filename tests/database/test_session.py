# coding utf-8
# ᛝ

from unittest.mock import Mock

import pytest

from database.session import DatabaseSession


def test_open_creates_database_from_schema_and_sets_pragmas(tmp_path, monkeypatch):
    database_path = tmp_path / 'data' / 'receipt.db'
    schema_path = tmp_path / 'schema.sql'
    schema_path.write_text('CREATE TABLE sample(id INTEGER);', encoding='utf-8')
    connection = Mock()
    monkeypatch.setattr('database.session.sqlite3.connect', Mock(return_value=connection))

    database = DatabaseSession(database_path, schema_path, Mock())
    database.open()

    connection.executescript.assert_called_once_with('CREATE TABLE sample(id INTEGER);')
    assert [call.args[0] for call in connection.execute.call_args_list] == [
        'PRAGMA foreign_keys = ON',
        'PRAGMA journal_mode = WAL'
    ]
    assert connection.commit.call_count == 1
    assert database.session is connection


def test_close_closes_injected_connection(tmp_path, monkeypatch):
    database_path = tmp_path / 'receipt.db'
    database_path.touch()
    connection = Mock()
    monkeypatch.setattr('database.session.sqlite3.connect', Mock(return_value=connection))

    database = DatabaseSession(database_path, tmp_path / 'unused.sql', Mock())
    database.open()
    database.close()

    connection.close.assert_called_once_with()


def test_open_does_not_continue_with_empty_database_when_schema_is_missing(tmp_path, monkeypatch):
    database_path = tmp_path / 'data' / 'receipt.db'
    connection = Mock()
    monkeypatch.setattr('database.session.sqlite3.connect', Mock(return_value=connection))
    logger = Mock()
    database = DatabaseSession(database_path, tmp_path / 'missing.sql', logger)

    with pytest.raises(FileNotFoundError, match='Database schema not found'):
        database.open()

    connection.close.assert_called_once_with()
    assert not database_path.exists()
