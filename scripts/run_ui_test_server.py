from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ia_v7 import create_app
from ia_v7.config import Settings


class UiTestOllama:
    def __init__(self, model_file: Path) -> None:
        self.model_file = model_file
        self.active = True
        self.models = ["gemma4:e4b", "modele-test:latest"]
        self.loaded = ["gemma4:e4b"]

    def get_default_model(self) -> str:
        if self.model_file.exists():
            return self.model_file.read_text(encoding="utf-8").strip()
        return "gemma4:e4b"

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
        self.active = True

    def stop_server(self):
        self.active = False
        self.loaded = []

    def load_model(self, model):
        self.loaded = [model]
        return {"done": True}

    def unload_model(self, model):
        self.loaded = [loaded for loaded in self.loaded if loaded != model]
        return {"done": True}

    def chat_stream(self, model, messages):
        prompt = messages[-1]["content"]
        if "LIVRABLE_TEST" in prompt:
            answer = "```livrable\nContenu livrable automatisé\n```"
        elif "MARKDOWN_TEST" in prompt:
            answer = "# Titre test\n\n- élément un\n- élément deux\n\n```python\nprint('ok')\n```\n<script>window.__xss_test = true</script>"
        elif "GENERATION_LONGUE_TEST" in prompt:
            for index in range(80):
                time.sleep(0.05)
                yield json.dumps(
                    {"message": {"content": f"fragment-{index} "}, "done": False}
                )
            yield json.dumps({"done": True})
            return
        elif "ERREUR_RESEAU_TEST" in prompt:
            raise RuntimeError("Erreur réseau simulée")
        else:
            answer = "TEST OK"
        for chunk in (answer[: len(answer) // 2], answer[len(answer) // 2 :]):
            if chunk:
                yield json.dumps({"message": {"content": chunk}, "done": False})
        yield json.dumps({"done": True})

    def chat_complete(self, model, messages):
        if "titre court" in messages[-1]["content"]:
            return "Titre automatique test"
        return '{"faits": []}'


def main() -> None:
    data_dir = ROOT / ".tmp_ui_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    database_path = data_dir / "ia-ui-test.db"
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{database_path}{suffix}")
        if candidate.exists():
            candidate.unlink()
    shutil.rmtree(data_dir / "exports", ignore_errors=True)

    settings = replace(
        Settings.from_env(),
        data_dir=data_dir,
        database_path=database_path,
        default_model_path=data_dir / "default_model.txt",
        export_dir=data_dir / "exports",
        host="127.0.0.1",
        port=4174,
    )
    app = create_app(settings=settings, ollama_client=UiTestOllama(settings.default_model_path))
    app.run(host=settings.host, port=settings.port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
