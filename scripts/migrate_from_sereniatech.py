from __future__ import annotations

import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_v7.infrastructure.database import Database


TABLES = ("ia_dossiers", "ia_conversations", "ia_messages", "ia_faits")


def _open_read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]


def migrate(
    source: Path,
    target: Path,
    replace: bool = False,
    skip_orphans: bool = False,
) -> dict[str, dict[str, int]]:
    source = Path(source).resolve()
    target = Path(target).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Base source introuvable : {source}")
    if target.exists() and not replace:
        raise FileExistsError(
            f"La cible existe déjà : {target}. Utiliser --replace pour la remplacer."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f"{target.name}.importing")
    if temporary.exists():
        temporary.unlink()

    counts: dict[str, int] = {}
    skipped: dict[str, int] = {}
    try:
        Database(temporary).initialize()
        with closing(_open_read_only(source)) as source_connection, closing(
            sqlite3.connect(temporary)
        ) as target_connection:
            target_connection.execute("PRAGMA foreign_keys = OFF")
            valid_conversation_ids = {
                row[0]
                for row in source_connection.execute(
                    "SELECT id FROM ia_conversations WHERE dossier_id IS NULL "
                    "OR dossier_id IN (SELECT id FROM ia_dossiers)"
                )
            }
            for table in TABLES:
                columns = _columns(source_connection, table)
                if not columns:
                    raise RuntimeError(f"Table source absente : {table}")
                target_columns = set(_columns(target_connection, table))
                if not set(columns).issubset(target_columns):
                    missing = sorted(set(columns) - target_columns)
                    raise RuntimeError(f"Colonnes incompatibles pour {table} : {missing}")
                rows = source_connection.execute(f"SELECT * FROM {table}").fetchall()
                original_count = len(rows)
                if skip_orphans and table == "ia_conversations":
                    rows = [row for row in rows if row["id"] in valid_conversation_ids]
                elif skip_orphans and table in {"ia_messages", "ia_faits"}:
                    rows = [
                        row
                        for row in rows
                        if row["conversation_id"] in valid_conversation_ids
                    ]
                names = ", ".join(columns)
                placeholders = ", ".join("?" for _ in columns)
                target_connection.executemany(
                    f"INSERT INTO {table} ({names}) VALUES ({placeholders})",
                    ([row[column] for column in columns] for row in rows),
                )
                counts[table] = len(rows)
                skipped[table] = original_count - len(rows)
            target_connection.commit()
            target_connection.execute("PRAGMA foreign_keys = ON")
            violations = target_connection.execute("PRAGMA foreign_key_check").fetchall()
            integrity = target_connection.execute("PRAGMA integrity_check").fetchone()[0]
            if violations:
                raise RuntimeError(f"Relations invalides après import : {len(violations)}")
            if integrity != "ok":
                raise RuntimeError(f"Intégrité SQLite invalide : {integrity}")
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return {"copied": counts, "skipped": skipped}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copie uniquement les données IA d'une base SérénIA Tech."
    )
    parser.add_argument("source", type=Path, help="Chemin de sereniatech.db en lecture seule.")
    parser.add_argument(
        "--target", type=Path, default=ROOT / "data" / "ia.db", help="Base IA cible."
    )
    parser.add_argument("--replace", action="store_true", help="Remplace la base cible.")
    parser.add_argument(
        "--skip-orphans",
        action="store_true",
        help="Ignore les lignes dont la relation parente est absente.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = migrate(args.source, args.target, args.replace, args.skip_orphans)
    print(f"Migration terminée vers {args.target.resolve()}")
    for table, count in result["copied"].items():
        skipped = result["skipped"][table]
        suffix = f" (ignorés car orphelins : {skipped})" if skipped else ""
        print(f"- {table}: {count}{suffix}")


if __name__ == "__main__":
    main()
