from __future__ import annotations

import json
from typing import Any, Iterable

from ia_v7.infrastructure.repository import IaRepository
from .context import FactExtractor, build_context


DELIVERABLE_INSTRUCTION = (
    "Quand l'utilisateur te demande de produire, reformuler, traduire, résumer "
    "ou transformer un texte destiné à être réutilisé ailleurs (texte avec émojis, "
    "description, résumé, traduction, reformulation, message à copier-coller, etc.), "
    "tu dois impérativement placer ce texte final dans un bloc ```livrable\n...\n```, "
    "sans exception. N'écris jamais ce texte directement dans ta réponse en dehors de "
    "ce bloc. Ne mets pas de commentaires à l'intérieur du bloc."
)


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
        system_prompt = f"{base_prompt}\n\n{DELIVERABLE_INSTRUCTION}".strip()
        history = self.repository.list_messages(conversation_id)
        facts = self.repository.list_facts(conversation_id)
        messages = build_context(system_prompt, history, user_message, facts, self.num_ctx)
        if not conversation["ephemere"]:
            self.repository.append_message(conversation_id, "user", user_message)
        return conversation, model, messages

    def stream_chat(self, conversation_id: int, user_message: str) -> Iterable[str]:
        conversation, model, messages = self.prepare_chat(conversation_id, user_message)
        ephemeral = bool(conversation["ephemere"])
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
