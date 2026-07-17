from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_v7 import create_app
from ia_v7.config import Settings


def main() -> None:
    data_dir = ROOT / ".tmp_ui_data" / "real"
    data_dir.mkdir(parents=True, exist_ok=True)
    database_path = data_dir / "ia-ui-real.db"
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{database_path}{suffix}")
        if candidate.exists():
            candidate.unlink()
    settings = replace(
        Settings.from_env(),
        data_dir=data_dir,
        database_path=database_path,
        default_model_path=data_dir / "default_model.txt",
        captures_dir=data_dir / "captures",
        default_model="gemma4:e4b",
        host="127.0.0.1",
        port=4175,
    )
    app = create_app(settings=settings)
    app.run(host=settings.host, port=settings.port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()

