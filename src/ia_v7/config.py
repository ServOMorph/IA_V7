from __future__ import annotations

from dataclasses import dataclass, replace
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    data_dir: Path
    database_path: Path
    default_model_path: Path
    export_dir: Path
    captures_dir: Path
    ollama_url: str
    default_model: str
    num_ctx: int
    host: str
    port: int

    @classmethod
    def from_env(cls, **overrides: object) -> "Settings":
        data_dir = Path(os.getenv("IA_V7_DATA_DIR", PROJECT_ROOT / "data")).resolve()
        settings = cls(
            project_root=PROJECT_ROOT,
            data_dir=data_dir,
            database_path=Path(os.getenv("IA_V7_DATABASE", data_dir / "ia.db")).resolve(),
            default_model_path=Path(
                os.getenv("IA_V7_DEFAULT_MODEL_FILE", data_dir / "default_model.txt")
            ).resolve(),
            export_dir=Path(
                os.getenv("IA_V7_EXPORT_DIR", PROJECT_ROOT / "exports")
            ).resolve(),
            captures_dir=Path(
                os.getenv("IA_V7_CAPTURES_DIR", PROJECT_ROOT / "rapports_erreurs_manuels")
            ).resolve(),
            ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            default_model=os.getenv("IA_V7_DEFAULT_MODEL", "gemma4:e4b"),
            num_ctx=int(os.getenv("IA_V7_NUM_CTX", "16384")),
            host=os.getenv("IA_V7_HOST", "127.0.0.1"),
            port=int(os.getenv("IA_V7_PORT", "4023")),
        )
        return replace(settings, **overrides) if overrides else settings

