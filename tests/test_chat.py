import json

from ia_v7.services.chat import (
    CODE_FILE_INSTRUCTION,
    DELIVERABLE_INSTRUCTION,
    extract_file_blocks,
    write_file_blocks,
)


def test_deliverable_instruction_uses_real_newlines():
    assert "```livrable\n...\n```" in DELIVERABLE_INSTRUCTION
    assert "```livrable\\n...\\n```" not in DELIVERABLE_INSTRUCTION


def test_extract_file_blocks_single():
    content = "Voici :\n```fichier:app.py\nprint('hi')\n```\nVoila."
    assert extract_file_blocks(content) == [("app.py", "print('hi')")]


def test_extract_file_blocks_multiple():
    content = (
        "```fichier:a.py\ncontenu a\n```\n"
        "texte\n"
        "```fichier:sous/b.py\ncontenu b\n```"
    )
    assert extract_file_blocks(content) == [
        ("a.py", "contenu a"),
        ("sous/b.py", "contenu b"),
    ]


def test_write_file_blocks_creates_file(tmp_path):
    report = write_file_blocks(tmp_path, "```fichier:app.py\nprint('hi')\n```")
    assert "app.py" in report
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "print('hi')\n"


def test_write_file_blocks_creates_subdirectories(tmp_path):
    write_file_blocks(tmp_path, "```fichier:src/pkg/mod.py\ncontenu\n```")
    assert (tmp_path / "src" / "pkg" / "mod.py").read_text(encoding="utf-8") == "contenu\n"


def test_write_file_blocks_overwrites_existing(tmp_path):
    existing = tmp_path / "app.py"
    existing.write_text("ancien", encoding="utf-8")
    write_file_blocks(tmp_path, "```fichier:app.py\nnouveau\n```")
    assert existing.read_text(encoding="utf-8") == "nouveau\n"


def test_write_file_blocks_rejects_path_traversal(tmp_path):
    report = write_file_blocks(tmp_path, "```fichier:../hors.py\ncontenu\n```")
    assert "hors du dossier de travail" in report
    assert not (tmp_path.parent / "hors.py").exists()


def test_write_file_blocks_no_block_returns_empty(tmp_path):
    assert write_file_blocks(tmp_path, "Réponse normale sans bloc.") == ""


def make_code_folder(repository, tmp_path):
    return repository.create_folder("Espace code", mode="code", work_path=str(tmp_path))


def test_prepare_chat_adds_code_instruction_for_code_folder(app, tmp_path):
    with app.app_context():
        extensions = app.extensions["ia_v7"]
        repository = extensions["repository"]
        folder = make_code_folder(repository, tmp_path)
        conversation = repository.create_conversation(
            "", "modele-test", False, folder["id"]
        )
        _, _, messages = extensions["chat_service"].prepare_chat(
            conversation["id"], "Crée un fichier app.py"
        )
    assert CODE_FILE_INSTRUCTION in messages[0]["content"]


def test_prepare_chat_no_code_instruction_for_chat_folder(app):
    with app.app_context():
        extensions = app.extensions["ia_v7"]
        repository = extensions["repository"]
        conversation = repository.create_conversation("", "modele-test", False, None)
        _, _, messages = extensions["chat_service"].prepare_chat(
            conversation["id"], "Bonjour"
        )
    assert CODE_FILE_INSTRUCTION not in messages[0]["content"]


def test_stream_chat_writes_file_block_in_code_folder(app, tmp_path):
    with app.app_context():
        extensions = app.extensions["ia_v7"]
        repository = extensions["repository"]
        folder = make_code_folder(repository, tmp_path)
        conversation = repository.create_conversation(
            "", "modele-test", False, folder["id"]
        )
        extensions["ollama"].chat_stream = lambda model, messages: iter(
            [
                json.dumps(
                    {
                        "message": {
                            "content": "```fichier:app.py\nprint('hi')\n```"
                        },
                        "done": False,
                    }
                ),
                json.dumps({"done": True}),
            ]
        )
        list(extensions["chat_service"].stream_chat(conversation["id"], "Crée app.py"))
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "print('hi')\n"
