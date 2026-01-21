# coding utf-8
# ᛝ

import logging
from pathlib import Path
import sqlite3


class DatabaseSession:
    def __init__(self, database_path: Path, schema_path: Path, logger: logging.Logger):
        self._database_path = database_path
        self._schema_path = schema_path
        self._logger = logger
        self._session: sqlite3.Connection | None = None
    
    def open(self) -> None:
        if self._session is not None:
            return
        
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        
        database_exists = self._database_path.exists()
        if not database_exists:
            self._logger.warning(
                'Database does not exist on path: %s',
                self._database_path
            )
            try:
                self._session = sqlite3.connect(self._database_path)
                self._session.row_factory = sqlite3.Row
                self._create_db()
                self._logger.info(
                    'Database successfully created'
                )
            except Exception:
                self._logger.exception(
                    'Failed to create database on path: %s',
                    self._database_path
                )
                self.close()
                try:
                    self._database_path.unlink(missing_ok=True)
                except OSError:
                    self._logger.warning(
                        'Failed to remove database on path: %s',
                        self._database_path
                    )
                    raise
                raise
        
        if self._session is None:
            self._session = sqlite3.connect(self._database_path)
            self._session.row_factory = sqlite3.Row

        self._session.execute("PRAGMA foreign_keys = ON")
        self._session.execute("PRAGMA journal_mode = WAL")
    
    def _create_db(self) -> None:
        if not self._schema_path.exists():
            raise FileNotFoundError(
                f"Database schema not found: {self._schema_path}"
            )
        
        sql = self._schema_path.read_text(encoding="utf-8")
        
        self._session.executescript(sql)
        self._session.commit()

    def close(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None
    
    @property
    def session(self) -> sqlite3.Connection:
        if self._session is None:
            raise RuntimeError("DB session is not opened")

        return self._session
    
