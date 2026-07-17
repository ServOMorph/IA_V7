from __future__ import annotations

import hashlib
import sqlite3
from typing import Any, Iterable

from .database import Database


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


class IaRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list_folders(self) -> list[dict[str, Any]]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT * FROM ia_dossiers ORDER BY nom COLLATE NOCASE"
            ).fetchall()
        return [dict(row) for row in rows]

    def create_folder(self, name: str, system_prompt: str = "") -> dict[str, Any]:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO ia_dossiers (nom, system_prompt) VALUES (?, ?)",
                (name, system_prompt),
            )
            row = connection.execute(
                "SELECT * FROM ia_dossiers WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def update_folder(self, folder_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
        assignments = ", ".join(f"{field} = ?" for field in fields)
        with self.database.transaction() as connection:
            cursor = connection.execute(
                f"UPDATE ia_dossiers SET {assignments} WHERE id = ?",
                (*fields.values(), folder_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT * FROM ia_dossiers WHERE id = ?", (folder_id,)
            ).fetchone()
        return dict(row)

    def delete_folder(self, folder_id: int) -> bool:
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM ia_dossiers WHERE id = ?", (folder_id,))
        return cursor.rowcount > 0

    def list_conversations(self, folder_id: int | None = None) -> list[dict[str, Any]]:
        with self.database.session() as connection:
            if folder_id is None:
                rows = connection.execute(
                    "SELECT * FROM ia_conversations ORDER BY date_maj DESC, id DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM ia_conversations WHERE dossier_id = ? "
                    "ORDER BY date_maj DESC, id DESC",
                    (folder_id,),
                ).fetchall()
        return [dict(row) for row in rows]

    def get_conversation(self, conversation_id: int, include_messages: bool = False) -> dict[str, Any] | None:
        with self.database.session() as connection:
            row = connection.execute(
                "SELECT * FROM ia_conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if row is None:
                return None
            conversation = dict(row)
            if include_messages:
                messages = connection.execute(
                    "SELECT * FROM ia_messages WHERE conversation_id = ? ORDER BY id",
                    (conversation_id,),
                ).fetchall()
                conversation["messages"] = [dict(message) for message in messages]
        return conversation

    def create_conversation(
        self,
        title: str,
        model: str,
        ephemeral: bool,
        folder_id: int | None,
    ) -> dict[str, Any]:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "INSERT INTO ia_conversations (dossier_id, titre, modele, ephemere) "
                "VALUES (?, ?, ?, ?)",
                (folder_id, title, model, int(ephemeral)),
            )
            row = connection.execute(
                "SELECT * FROM ia_conversations WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def update_conversation(self, conversation_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
        assignments = ", ".join(f"{field} = ?" for field in fields)
        with self.database.transaction() as connection:
            cursor = connection.execute(
                f"UPDATE ia_conversations SET {assignments}, date_maj = CURRENT_TIMESTAMP "
                "WHERE id = ?",
                (*fields.values(), conversation_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT * FROM ia_conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return dict(row)

    def delete_conversation(self, conversation_id: int) -> bool:
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "DELETE FROM ia_conversations WHERE id = ?", (conversation_id,)
            )
        return cursor.rowcount > 0

    def list_messages(self, conversation_id: int) -> list[dict[str, Any]]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT * FROM ia_messages WHERE conversation_id = ? ORDER BY id",
                (conversation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def append_message(self, conversation_id: int, role: str, content: str) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO ia_messages (conversation_id, role, contenu) VALUES (?, ?, ?)",
                (conversation_id, role, content),
            )
            connection.execute(
                "UPDATE ia_conversations SET date_maj = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,),
            )

    def get_system_prompt(self, folder_id: int | None) -> str:
        if folder_id is None:
            return ""
        with self.database.session() as connection:
            row = connection.execute(
                "SELECT system_prompt FROM ia_dossiers WHERE id = ?", (folder_id,)
            ).fetchone()
        return (row["system_prompt"] if row else "") or ""

    def list_facts(self, conversation_id: int) -> list[dict[str, Any]]:
        with self.database.session() as connection:
            rows = connection.execute(
                "SELECT categorie, fait FROM ia_faits WHERE conversation_id = ? ORDER BY id",
                (conversation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_facts(self, conversation_id: int, facts: Iterable[dict[str, Any]]) -> int:
        inserted = 0
        with self.database.transaction() as connection:
            for fact in facts:
                category = fact.get("categorie")
                value = str(fact["fait"])
                digest = hashlib.md5(
                    f"{conversation_id}|{category or ''}|{value.lower()}".encode("utf-8")
                ).hexdigest()
                try:
                    connection.execute(
                        "INSERT INTO ia_faits (conversation_id, categorie, fait, hash_md5) "
                        "VALUES (?, ?, ?, ?)",
                        (conversation_id, category, value, digest),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass
        return inserted

