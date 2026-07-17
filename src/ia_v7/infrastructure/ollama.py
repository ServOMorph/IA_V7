from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Iterable

import requests


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        default_model_path: Path,
        fallback_model: str,
        num_ctx: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_model_path = Path(default_model_path)
        self.fallback_model = fallback_model
        self.num_ctx = num_ctx
        self._server_process: subprocess.Popen[bytes] | None = None

    def get_default_model(self) -> str:
        try:
            model = self.default_model_path.read_text(encoding="utf-8").strip()
            return model or self.fallback_model
        except OSError:
            return self.fallback_model

    def set_default_model(self, model: str) -> None:
        self.default_model_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.default_model_path.with_suffix(".tmp")
        temporary.write_text(model, encoding="utf-8")
        os.replace(temporary, self.default_model_path)

    def status(self) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = [
                model.get("name")
                for model in response.json().get("models", [])
                if model.get("name")
            ]
            return {"actif": True, "modeles": models}
        except requests.RequestException as error:
            return {"actif": False, "modeles": [], "error": str(error)}

    def is_server_active(self, timeout: int = 2) -> bool:
        try:
            return requests.get(f"{self.base_url}/api/tags", timeout=timeout).status_code == 200
        except requests.RequestException:
            return False

    def loaded_models(self, timeout: int = 5) -> list[dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/api/ps", timeout=timeout)
            response.raise_for_status()
            return response.json().get("models", [])
        except requests.RequestException:
            return []

    def start_server(self) -> None:
        executable = shutil.which("ollama")
        if executable is None:
            raise RuntimeError("La commande Ollama est introuvable dans PATH.")
        if self.is_server_active():
            return
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        self._server_process = subprocess.Popen(
            [executable, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )

    def stop_server(self) -> None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/IM", "ollama.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        elif self._server_process is not None and self._server_process.poll() is None:
            self._server_process.terminate()

    def load_model(self, model: str, timeout: int = 300) -> dict[str, Any]:
        return self._generate_lifecycle(model, keep_alive=-1, timeout=timeout)

    def unload_model(self, model: str, timeout: int = 30) -> dict[str, Any]:
        return self._generate_lifecycle(model, keep_alive=0, timeout=timeout)

    def _generate_lifecycle(self, model: str, keep_alive: int, timeout: int) -> dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": "",
                "keep_alive": keep_alive,
                "options": {"num_ctx": self.num_ctx},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        timeout: int = 600,
    ) -> Iterable[str]:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                "keep_alive": -1,
                "options": {"num_ctx": self.num_ctx},
            },
            stream=True,
            timeout=timeout,
        )
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if line:
                yield line

    def chat_complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        timeout: int = 120,
    ) -> str:
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "keep_alive": -1,
                "options": {"num_ctx": self.num_ctx},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

