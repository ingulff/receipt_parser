# coding utf-8
# ᛝ

from contextlib import contextmanager
from pathlib import Path
import sqlite3


def preInit(database_path:str):
    db_path = Path(database_path)
    sql_script_path = Path("./database/sql/create_database.sql")

    if not (sql_script_path.exists()):
        raise FileNotFoundError("sql not found in path: ./sql/create_database.sql")

    with sqlite3.connect(db_path) as session:
        has_tables = session.execute(
            """
            SELECT
                name
            FROM
                sqlite_master
            WHERE
                type='table'
            LIMIT 1
            """
        ).fetchone() is not None
        if not has_tables:
            sql = sql_script_path.read_text(encoding="utf-8")
            session.executescript(sql)



class DatabaseSession:
    def __init__(self, database_path: str):
        self._database_path = database_path
        self._session: sqlite3.Connection | None = None

    def open(self) -> None:
        preInit(self._database_path) # todo
        if self._session is None:
            self._session = sqlite3.connect(self._database_path)
            self._session.row_factory = sqlite3.Row
            self._session.execute("PRAGMA foreign_keys = ON")
            self._session.execute("PRAGMA journal_mode = WAL")
    
    def close(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    @property
    def session(self) -> sqlite3.Connection:
        if self._session is None:
            raise RuntimeError("DB session is not opened")

        return self._session
    