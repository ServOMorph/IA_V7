from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
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
    raw_text: str = ""

    @property
    def raw_payload(self) -> str:
        stripped = self.raw_text.strip()
        return re.sub(r"^/\S+[ \t]*", "", stripped, count=1).strip()


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


SENSITIVE_PLACEHOLDER = "[DONNÉE_SENSIBLE]"

EMAIL_PATTERN = re.compile(
    r"[\w.+-]+(?:@|＠)[\w-]+(?:(?:\.|．)[\w-]+)+",
    re.IGNORECASE,
)
IBAN_CANDIDATE_PATTERN = re.compile(
    r"(?<![A-Z0-9])[A-Z]{2}\d{2}"
    r"(?:[ \u00a0\u200b-\u200d\ufeff]*[A-Z0-9]){11,30}"
    r"(?![A-Z0-9])",
    re.IGNORECASE | re.ASCII,
)
CARD_PATTERN = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
ADDRESS_WITH_CITY_PATTERN = re.compile(
    r"\b\d{1,4}\s?(?:(?i:bis|ter))?,?\s+"
    r"(?i:rue|avenue|av\.|boulevard|bd|impasse|allée|allee|chemin|place|quai)"
    r"\s+[^,\n.;]+,\s*\d{5}\s+"
    r"[A-ZÀ-Ý][\w'’-]*(?:[ -][A-ZÀ-Ý][\w'’-]*){0,3}",
)
NIR_PATTERN = re.compile(
    r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?\d{2}\s?\d{3}\s?\d{3}"
    r"(?:\s?\d{2})?\b"
)
PHONE_PATTERN = re.compile(r"(?:\+33\s?|\b0)[1-9](?:[\s.-]?\d{2}){4}\b")
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,4}\s?(?:bis|ter)?,?\s+"
    r"(?:rue|avenue|av\.|boulevard|bd|impasse|allée|allee|chemin|place|quai)"
    r"\s+[^,\n.;]+",
    re.IGNORECASE,
)
NAME_PATTERN = re.compile(
    r"\b(?:M\.|Mr|Mme|Mlle|Dr|Me)\s+[A-ZÀ-Ý][\w'’-]+"
    r"(?:\s+[A-ZÀ-Ý][\w'’-]+)?"
)

SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    EMAIL_PATTERN,
    NIR_PATTERN,
    PHONE_PATTERN,
    ADDRESS_WITH_CITY_PATTERN,
    ADDRESS_PATTERN,
    NAME_PATTERN,
]


def _compact_iban(value: str) -> str:
    return re.sub(r"[ \u00a0\u200b-\u200d\ufeff]", "", value).upper()


def _is_valid_iban(value: str) -> bool:
    compact = _compact_iban(value)
    if not re.fullmatch(
        r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", compact, flags=re.ASCII
    ):
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = "".join(
        str(ord(character) - ord("A") + 10) if character.isalpha() else character
        for character in rearranged
    )
    return int(numeric) % 97 == 1


def _replace_iban_candidates(text: str) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        candidate = match.group(0)
        alphanumeric_positions = [
            index + 1 for index, character in enumerate(candidate) if character.isalnum()
        ]
        for compact_length in range(min(34, len(alphanumeric_positions)), 14, -1):
            end = alphanumeric_positions[compact_length - 1]
            prefix = candidate[:end]
            if _is_valid_iban(prefix):
                count += 1
                return SENSITIVE_PLACEHOLDER + candidate[end:]
        return candidate

    return IBAN_CANDIDATE_PATTERN.sub(replace, text), count


def _passes_luhn(value: str) -> bool:
    digits = [int(character) for character in value if character.isdigit()]
    if len(digits) != 16:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _is_valid_ipv4(value: str) -> bool:
    try:
        return ipaddress.ip_address(value).version == 4
    except ValueError:
        return False


def _replace_validated(
    text: str,
    pattern: re.Pattern[str],
    validator: Callable[[str], bool],
) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        value = match.group(0)
        if not validator(value):
            return value
        count += 1
        return SENSITIVE_PLACEHOLDER

    return pattern.sub(replace, text), count


def anonymize_text(text: str) -> tuple[str, int]:
    total = 0
    text, count = EMAIL_PATTERN.subn(SENSITIVE_PLACEHOLDER, text)
    total += count
    text, count = _replace_iban_candidates(text)
    total += count
    for pattern in (NIR_PATTERN, PHONE_PATTERN):
        text, count = pattern.subn(SENSITIVE_PLACEHOLDER, text)
        total += count
    text, count = _replace_validated(text, CARD_PATTERN, _passes_luhn)
    total += count
    text, count = _replace_validated(text, IPV4_PATTERN, _is_valid_ipv4)
    total += count
    for pattern in (ADDRESS_WITH_CITY_PATTERN, ADDRESS_PATTERN, NAME_PATTERN):
        text, count = pattern.subn(SENSITIVE_PLACEHOLDER, text)
        total += count
    return text, total


_PATH_HINT = re.compile(r"^[^\s]+$")


def _looks_like_path(payload: str) -> bool:
    if not _PATH_HINT.fullmatch(payload):
        return False
    return "/" in payload or "\\" in payload or bool(re.search(r"\.\w{1,10}$", payload))


def _handle_rgpd(context: CommandContext) -> CommandResult:
    payload = context.raw_payload
    if not payload:
        return CommandResult(
            False,
            "Usage : /rgpd <chemin_fichier> ou /rgpd <texte à anonymiser>",
        )

    candidate = Path(_strip_quotes(payload))
    single_token = "\n" not in payload and _PATH_HINT.fullmatch(_strip_quotes(payload))

    if single_token and candidate.is_file():
        try:
            content = candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return CommandResult(
                False,
                f"Format invalide : {candidate} n'est pas un fichier texte UTF-8",
            )
        except OSError as error:
            return CommandResult(False, f"Lecture impossible : {candidate} ({error})")

        anonymized, count = anonymize_text(content)
        target = candidate.with_name(f"{candidate.stem}_anonymise.md")
        if target.exists():
            return CommandResult(False, f"Le fichier existe déjà : {target}")
        try:
            target.write_text(anonymized, encoding="utf-8")
        except OSError as error:
            return CommandResult(False, f"Écriture impossible : {target} ({error})")
        return CommandResult(
            True,
            f"{count} donnée(s) sensible(s) remplacée(s).\nFichier anonymisé écrit : {target}",
        )

    if single_token and _looks_like_path(_strip_quotes(payload)):
        return CommandResult(False, f"Fichier non trouvé : {_strip_quotes(payload)}")

    anonymized, count = anonymize_text(payload)
    return CommandResult(
        True,
        f"{count} donnée(s) sensible(s) remplacée(s).\n\n{anonymized}",
    )


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
        self.registry.register(
            "rgpd",
            "Anonymise les PII (emails, téléphones, NIR, IBAN, CB, IP, adresses, "
            "noms avec civilité) : /rgpd <chemin_fichier> ou /rgpd <texte>. "
            "Depuis un fichier, écrit <original>_anonymise.md à côté. "
            "Limite : les noms sans civilité ne sont pas détectés.",
            _handle_rgpd,
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
            conversation_id, args, self.repository, self.registry, self.export_dir, text
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
