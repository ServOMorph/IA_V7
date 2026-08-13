from __future__ import annotations

import sqlite3

from ia_v7.infrastructure.database import Database


def test_initialize_migrates_existing_folder_table(tmp_path):
    path = tmp_path / "ia.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE ia_dossiers ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "nom TEXT NOT NULL, "
            "system_prompt TEXT NOT NULL DEFAULT '', "
            "date_creation DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.execute("INSERT INTO ia_dossiers (nom) VALUES ('Projet existant')")

    Database(path).initialize()

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT nom, mode, chemin_travail FROM ia_dossiers"
        ).fetchone()
    assert row == ("Projet existant", "chat", "")
