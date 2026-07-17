from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_v7 import create_app
from ia_v7.config import Settings


class FakeOllama:
    def __init__(self, model_file: Path) -> None:
        self.model_file = model_file
        self.active = True
        self.models = ["modele-test:latest", "autre:1b"]
        self.loaded = ["modele-test:latest"]
        self.started = False
        self.stopped = False
        self.loaded_requests: list[str] = []
        self.unloaded_requests: list[str] = []

    def get_default_model(self) -> str:
        return self.model_file.read_text(encoding="utf-8").strip() if self.model_file.exists() else self.models[0]

    def set_default_model(self, model: str) -> None:
        self.model_file.parent.mkdir(parents=True, exist_ok=True)
        self.model_file.write_text(model, encoding="utf-8")

    def status(self):
        return {"actif": self.active, "modeles": self.models if self.active else []}

    def is_server_active(self, timeout=2):
        return self.active

    def loaded_models(self, timeout=5):
        return [{"name": model} for model in self.loaded] if self.active else []

    def start_server(self):
        self.started = True
        self.active = True

    def stop_server(self):
        self.stopped = True
        self.active = False

    def load_model(self, model):
        self.loaded_requests.append(model)
        return {"done": True}

    def unload_model(self, model):
        self.unloaded_requests.append(model)
        return {"done": True}

    def chat_stream(self, model, messages):
        yield json.dumps({"message": {"content": "Bonjour "}, "done": False})
        yield json.dumps({"message": {"content": "depuis IA V7"}, "done": False})
        yield json.dumps({"done": True})

    def chat_complete(self, model, messages):
        if "titre court" in messages[-1]["content"]:
            return '"Titre de test"'
        return '{"faits": []}'


@pytest.fixture()
def fake_ollama(tmp_path):
    return FakeOllama(tmp_path / "default_model.txt")


@pytest.fixture()
def app(tmp_path, fake_ollama):
    base = Settings.from_env()
    settings = replace(
        base,
        data_dir=tmp_path,
        database_path=tmp_path / "test.db",
        default_model_path=tmp_path / "default_model.txt",
        export_dir=tmp_path / "exports",
        captures_dir=tmp_path / "captures",
    )
    application = create_app(settings=settings, ollama_client=fake_ollama)
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()

