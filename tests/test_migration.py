from pathlib import Path
import sqlite3

import pytest

from ia_v7.infrastructure.database import Database
from scripts.migrate_from_sereniatech import migrate


def test_migration_copies_only_ia_tables(tmp_path):
    source = tmp_path / "source.db"
    Database(source).initialize()
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE unrelated (secret TEXT)")
        connection.execute("INSERT INTO unrelated VALUES ('ne pas copier')")
        connection.execute("INSERT INTO ia_dossiers (nom) VALUES ('Dossier')")
        connection.execute("INSERT INTO ia_conversations (dossier_id, titre) VALUES (1, 'Conversation')")
        connection.execute("INSERT INTO ia_messages (conversation_id, role, contenu) VALUES (1, 'user', 'Bonjour')")
        connection.commit()

    target = tmp_path / "target.db"
    counts = migrate(source, target)
    assert counts == {
        "copied": {
            "ia_dossiers": 1,
            "ia_conversations": 1,
            "ia_messages": 1,
            "ia_faits": 0,
        },
        "skipped": {
            "ia_dossiers": 0,
            "ia_conversations": 0,
            "ia_messages": 0,
            "ia_faits": 0,
        },
    }
    with sqlite3.connect(target) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "unrelated" not in tables
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_migration_refuses_existing_target_without_replace(tmp_path):
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    Database(source).initialize()
    target.touch()
    with pytest.raises(FileExistsError):
        migrate(source, target)


def test_migration_can_skip_orphan_messages(tmp_path):
    source = tmp_path / "source.db"
    Database(source).initialize()
    with sqlite3.connect(source) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO ia_messages (conversation_id, role, contenu) VALUES (999, 'assistant', 'orphelin')"
        )
        connection.commit()
    target = tmp_path / "target.db"
    result = migrate(source, target, skip_orphans=True)
    assert result["copied"]["ia_messages"] == 0
    assert result["skipped"]["ia_messages"] == 1
