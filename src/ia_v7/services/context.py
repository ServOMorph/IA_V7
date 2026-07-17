from __future__ import annotations

import json
import re
import threading
from typing import Any

from ia_v7.infrastructure.repository import IaRepository


RESPONSE_MARGIN = 2048
FACT_PATTERNS = (
    (r"je m['’]appelle\s+([A-Za-zÀ-ÿ\-']+)", "identité"),
    (r"j['’]habite [àa]\s+([A-Za-zÀ-ÿ\-']+)", "identité"),
    (r"je pr[ée]f[èe]re\s+(.{2,40}?)(?:[.,\n]|$)", "préférence"),
    (r"j['’]utilise\s+(\S+)", "outil"),
    (r"je travaille sur\s+(.{2,40}?)(?:[.,\n]|$)", "projet"),
)
EXTRACTION_PROMPT = (
    "Extrais en JSON les faits nouveaux de cet échange qui méritent d'être mémorisés "
    "pour la suite de la conversation (nom, préférence, contrainte, décision, entité "
    "importante). Format : {\"faits\": [{\"categorie\": \"...\", \"fait\": \"...\"}]}. "
    "Si rien de nouveau : {\"faits\": []}. Max 5 faits, 10 mots chacun."
)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def build_sliding_context(
    system_prompt: str,
    history: list[dict[str, Any]],
    user_message: str,
    num_ctx: int = 16384,
) -> list[dict[str, str]]:
    budget = num_ctx - RESPONSE_MARGIN - estimate_tokens(system_prompt) - estimate_tokens(user_message)
    selected: list[dict[str, str]] = []
    index = len(history) - 1

    while index >= 1:
        newer = history[index]
        older = history[index - 1]
        newer_content = newer.get("contenu") or newer.get("content", "")
        older_content = older.get("contenu") or older.get("content", "")
        cost = estimate_tokens(older_content) + estimate_tokens(newer_content)
        if cost > budget:
            break
        selected = [
            {"role": older["role"], "content": older_content},
            {"role": newer["role"], "content": newer_content},
        ] + selected
        budget -= cost
        index -= 2

    if index == 0:
        message = history[0]
        content = message.get("contenu") or message.get("content", "")
        if estimate_tokens(content) <= budget:
            selected.insert(0, {"role": message["role"], "content": content})

    return [
        {"role": "system", "content": system_prompt},
        *selected,
        {"role": "user", "content": user_message},
    ]


def extract_facts_regex(text: str) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    for pattern, category in FACT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(1).strip().strip(".,;:!?")
            if value:
                facts.append({"categorie": category, "fait": value})
    return facts


def parse_llm_facts(raw: str) -> list[dict[str, str]]:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return []
    try:
        payload = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return []
    facts = payload.get("faits", []) if isinstance(payload, dict) else []
    return [fact for fact in facts if isinstance(fact, dict) and fact.get("fait")]


def format_facts(facts: list[dict[str, Any]]) -> str:
    if not facts:
        return ""
    lines = ["[Contexte de la conversation]"]
    lines.extend(f"- {fact.get('categorie') or 'info'}: {fact['fait']}" for fact in facts)
    return "\n".join(lines)


def build_context(
    system_prompt: str,
    history: list[dict[str, Any]],
    user_message: str,
    facts: list[dict[str, Any]],
    num_ctx: int,
) -> list[dict[str, str]]:
    facts_block = format_facts(facts)
    effective_prompt = f"{system_prompt}\n\n{facts_block}".strip() if facts_block else system_prompt
    return build_sliding_context(effective_prompt, history, user_message, num_ctx)


class FactExtractor:
    def __init__(self, repository: IaRepository, ollama: Any) -> None:
        self.repository = repository
        self.ollama = ollama

    def extract_with_llm(self, model: str, user_message: str, assistant_message: str) -> list[dict[str, str]]:
        raw = self.ollama.chat_complete(
            model,
            [
                {"role": "system", "content": EXTRACTION_PROMPT},
                {
                    "role": "user",
                    "content": f"user: {user_message}\nassistant: {assistant_message}",
                },
            ],
        )
        return parse_llm_facts(raw)

    def extract_and_persist_async(
        self,
        model: str,
        conversation_id: int,
        user_message: str,
        assistant_message: str,
    ) -> threading.Thread:
        def task() -> None:
            try:
                if not self.ollama.is_server_active():
                    return
                facts = extract_facts_regex(user_message)
                facts.extend(self.extract_with_llm(model, user_message, assistant_message))
                if facts:
                    self.repository.add_facts(conversation_id, facts)
            except Exception:
                return

        thread = threading.Thread(target=task, daemon=True, name=f"facts-{conversation_id}")
        thread.start()
        return thread

