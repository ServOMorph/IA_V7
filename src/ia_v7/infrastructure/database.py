from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS ia_dossiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    system_prompt TEXT NOT NULL DEFAULT '',
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ia_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dossier_id INTEGER,
    titre TEXT NOT NULL DEFAULT '',
    modele TEXT NOT NULL DEFAULT '',
    ephemere INTEGER NOT NULL DEFAULT 0 CHECK(ephemere IN (0, 1)),
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_maj DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dossier_id) REFERENCES ia_dossiers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ia_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    contenu TEXT NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES ia_conversations(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ia_faits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    categorie TEXT,
    fait TEXT NOT NULL,
    hash_md5 TEXT UNIQUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES ia_conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ia_messages_conversation
    ON ia_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_ia_conversations_dossier
    ON ia_conversations(dossier_id);
CREATE INDEX IF NOT EXISTS idx_ia_conversations_date_maj
    ON ia_conversations(date_maj DESC);
CREATE INDEX IF NOT EXISTS idx_ia_faits_conversation
    ON ia_faits(conversation_id);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as connection:
            connection.executescript(SCHEMA)
            connection.execute("PRAGMA journal_mode = WAL")

