from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from ia_v7.infrastructure.repository import IaRepository
from .context import FactExtractor, build_context


DELIVERABLE_INSTRUCTION = (
    "Quand l'utilisateur te demande explicitement un livrable ou un texte à "
    "copier-coller (il utilise des mots comme \"livrable\", \"à copier-coller\", "
    "\"le document final\", \"le texte final\"), tu dois placer ce texte dans un "
    "bloc ```livrable\n...\n```, sans exception. Dans tous les autres cas "
    "(conversation normale, reformulation, traduction, résumé sans demande "
    "explicite de livrable), réponds en texte normal, sans ce bloc. Ne mets pas "
    "de commentaires à l'intérieur du bloc."
)

CODE_FILE_INSTRUCTION = (
    "Quand l'utilisateur te demande explicitement de créer ou modifier un "
    "fichier, place son contenu complet dans un bloc "
    "```fichier:<chemin_relatif>\n...\n```, avec un bloc distinct par fichier et "
    "un chemin relatif au dossier de travail. N'utilise ce bloc que sur demande "
    "explicite de création ou modification de fichier."
)

FILE_BLOCK_PATTERN = re.compile(r"```fichier:([^\n`]+)\n(.*?)\n```", re.DOTALL)


def extract_file_blocks(content: str) -> list[tuple[str, str]]:
    return [
        (path.strip(), body)
        for path, body in FILE_BLOCK_PATTERN.findall(content)
        if path.strip()
    ]


def write_file_blocks(work_path: Path, content: str) -> str:
    blocks = extract_file_blocks(content)
    if not blocks:
        return ""
    root = work_path.resolve()
    written: list[str] = []
    errors: list[str] = []
    for raw_path, body in blocks:
        candidate = (root / raw_path).resolve()
        if candidate == root or not candidate.is_relative_to(root):
            errors.append(f"{raw_path} (hors du dossier de travail)")
            continue
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_text(body.strip() + "\n", encoding="utf-8")
            written.append(str(candidate.relative_to(root)))
        except OSError as error:
            errors.append(f"{raw_path} ({error})")
    lines: list[str] = []
    if written:
        lines.append("Fichier(s) écrit(s) : " + ", ".join(written))
    if errors:
        lines.append("Échec(s) : " + ", ".join(errors))
    return "\n\n" + "\n".join(lines) if lines else ""


class ChatService:
    def __init__(
        self,
        repository: IaRepository,
        ollama: Any,
        fact_extractor: FactExtractor,
        num_ctx: int,
    ) -> None:
        self.repository = repository
        self.ollama = ollama
        self.fact_extractor = fact_extractor
        self.num_ctx = num_ctx

    def prepare_chat(self, conversation_id: int, user_message: str) -> tuple[dict[str, Any], str, list[dict[str, str]]]:
        conversation = self.repository.get_conversation(conversation_id)
        if conversation is None:
            raise LookupError("Conversation introuvable")
        model = conversation["modele"] or self.ollama.get_default_model()
        base_prompt = self.repository.get_system_prompt(conversation["dossier_id"])
        system_prompt = f"{base_prompt}\n\n{DELIVERABLE_INSTRUCTION}"
        folder = self._code_folder(conversation)
        if folder is not None:
            system_prompt = f"{system_prompt}\n\n{CODE_FILE_INSTRUCTION}"
        system_prompt = system_prompt.strip()
        history = self.repository.list_messages(conversation_id)
        facts = self.repository.list_facts(conversation_id)
        messages = build_context(system_prompt, history, user_message, facts, self.num_ctx)
        if not conversation["ephemere"]:
            self.repository.append_message(conversation_id, "user", user_message)
        return conversation, model, messages

    def _code_folder(self, conversation: dict[str, Any]) -> dict[str, Any] | None:
        folder_id = conversation["dossier_id"]
        if folder_id is None:
            return None
        folder = self.repository.get_folder(folder_id)
        if folder is None or folder["mode"] != "code" or not folder["chemin_travail"]:
            return None
        return folder

    def stream_chat(self, conversation_id: int, user_message: str) -> Iterable[str]:
        conversation, model, messages = self.prepare_chat(conversation_id, user_message)
        ephemeral = bool(conversation["ephemere"])
        folder = self._code_folder(conversation)
        chunks: list[str] = []
        try:
            for line in self.ollama.chat_stream(model, messages):
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                chunk = payload.get("message", {}).get("content", "")
                if chunk:
                    chunks.append(chunk)
                    yield f"data: {json.dumps({'contenu': chunk}, ensure_ascii=False)}\n\n"
                if payload.get("done"):
                    break
            if folder is not None:
                report = write_file_blocks(Path(folder["chemin_travail"]), "".join(chunks))
                if report:
                    chunks.append(report)
                    yield f"data: {json.dumps({'contenu': report}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'fin': True})}\n\n"
        except Exception as error:
            yield f"data: {json.dumps({'erreur': str(error)}, ensure_ascii=False)}\n\n"
        finally:
            answer = "".join(chunks)
            if answer and not ephemeral:
                self.repository.append_message(conversation_id, "assistant", answer)
                self.fact_extractor.extract_and_persist_async(
                    model, conversation_id, user_message, answer
                )

    def generate_title(self, conversation_id: int) -> str:
        conversation = self.repository.get_conversation(conversation_id)
        if conversation is None:
            raise LookupError("Conversation introuvable")
        if conversation["ephemere"]:
            raise ValueError("Conversation éphémère")
        messages = self.repository.list_messages(conversation_id)[:2]
        if not messages:
            raise ValueError("Aucun message")
        exchange = "\n".join(f"{message['role']}: {message['contenu']}" for message in messages)
        prompt = (
            "Résume cet échange en un titre court de 3 à 5 mots, sans guillemets "
            f"ni ponctuation finale.\n\n{exchange}"
        )
        model = conversation["modele"] or self.ollama.get_default_model()
        raw_title = self.ollama.chat_complete(
            model, [{"role": "user", "content": prompt}]
        ).strip()
        title = raw_title.strip('"').strip().splitlines()[0][:80] if raw_title else ""
        if not title:
            raise RuntimeError("Titre vide")
        self.repository.update_conversation(conversation_id, {"titre": title})
        return title
