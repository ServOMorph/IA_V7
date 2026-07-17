from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
import shlex
from pathlib import Path
from typing import Callable, Iterable

from ia_v7.infrastructure.repository import IaRepository


@dataclass(frozen=True, slots=True)
class CommandResult:
    success: bool
    message: str


@dataclass(frozen=True, slots=True)
class CommandContext:
    conversation_id: int
    args: list[str]
    repository: IaRepository
    registry: "CommandRegistry"
    export_dir: Path


CommandHandler = Callable[[CommandContext], CommandResult]


@dataclass(frozen=True, slots=True)
class Command:
    name: str
    description: str
    handler: CommandHandler


@dataclass(slots=True)
class CommandRegistry:
    _commands: dict[str, Command] = field(default_factory=dict)

    def register(self, name: str, description: str, handler: CommandHandler) -> None:
        self._commands[name] = Command(name, description, handler)

    def get(self, name: str) -> Command | None:
        return self._commands.get(name)

    def list_commands(self) -> list[Command]:
        return sorted(self._commands.values(), key=lambda command: command.name)


def _strip_quotes(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def parse_command(text: str) -> tuple[str, list[str]] | None:
    stripped = text.strip()
    if not stripped.startswith("/"):
        return None
    body = stripped[1:]
    if not body.strip():
        return None
    try:
        parts = [_strip_quotes(part) for part in shlex.split(body, posix=False)]
    except ValueError:
        parts = body.split()
    if not parts:
        return None
    return parts[0].lower(), parts[1:]


def is_command(text: str) -> bool:
    return parse_command(text) is not None


def _handle_help(context: CommandContext) -> CommandResult:
    lines = ["Commandes disponibles :"]
    lines += [
        f"/{command.name} - {command.description}"
        for command in context.registry.list_commands()
    ]
    return CommandResult(True, "\n".join(lines))


LIVRABLE_PATTERN = re.compile(r"```livrable\s*\n(.*?)\n```", re.DOTALL)


def _extract_deliverable(content: str) -> str:
    matches = LIVRABLE_PATTERN.findall(content)
    if matches:
        return matches[-1].strip()
    return content.strip()


def _handle_write(context: CommandContext) -> CommandResult:
    if not context.args:
        return CommandResult(False, "Usage : /write <nom_fichier> [<path>]")
    name = context.args[0]
    directory = Path(context.args[1]) if len(context.args) > 1 else context.export_dir

    messages = context.repository.list_messages(context.conversation_id)
    assistant_messages = [message for message in messages if message["role"] == "assistant"]
    if not assistant_messages:
        return CommandResult(False, "Aucun message assistant dans la conversation")
    content = _extract_deliverable(assistant_messages[-1]["contenu"])
    if not content:
        return CommandResult(False, "Contenu vide, rien à écrire")

    filename = name if name.lower().endswith(".md") else f"{name}.md"
    target = directory / filename
    if target.exists():
        return CommandResult(False, f"Le fichier existe déjà : {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return CommandResult(True, f"Fichier écrit : {target}")


class CommandService:
    def __init__(self, repository: IaRepository, export_dir: Path) -> None:
        self.repository = repository
        self.export_dir = export_dir
        self.registry = CommandRegistry()
        self.registry.register("help", "Liste les commandes disponibles", _handle_help)
        self.registry.register(
            "write",
            "Enregistre le dernier livrable dans un fichier : /write <nom_fichier> [<path>]",
            _handle_write,
        )

    def execute(self, conversation_id: int, text: str) -> CommandResult:
        parsed = parse_command(text)
        if parsed is None:
            return CommandResult(False, "Ce message n'est pas une commande")
        name, args = parsed
        command = self.registry.get(name)
        if command is None:
            return CommandResult(False, f"Commande inconnue : /{name}")
        context = CommandContext(
            conversation_id, args, self.repository, self.registry, self.export_dir
        )
        return command.handler(context)

    def stream_execute(self, conversation_id: int, text: str) -> Iterable[str]:
        conversation = self.repository.get_conversation(conversation_id)
        ephemeral = bool(conversation["ephemere"]) if conversation else False
        if conversation and not ephemeral:
            self.repository.append_message(conversation_id, "user", text)
        result = self.execute(conversation_id, text)
        if result.success:
            yield f"data: {json.dumps({'contenu': result.message}, ensure_ascii=False)}\n\n"
            if conversation and not ephemeral:
                self.repository.append_message(conversation_id, "assistant", result.message)
        else:
            yield f"data: {json.dumps({'erreur': result.message}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'fin': True})}\n\n"
