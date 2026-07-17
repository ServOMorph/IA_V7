from __future__ import annotations

from ia_v7.services.commands import CommandService, is_command, parse_command


def create_conversation(client, **data):
    response = client.post("/api/ia/conversations", json=data)
    assert response.status_code == 201
    return response.get_json()


def test_parse_command():
    assert parse_command("/help") == ("help", [])
    assert parse_command("/write rapport data") == ("write", ["rapport", "data"])
    assert parse_command("Bonjour") is None
    assert parse_command("  /help  ") == ("help", [])
    assert parse_command("/") is None


def test_is_command():
    assert is_command("/help")
    assert not is_command("Bonjour le monde")


def make_service(app):
    with app.app_context():
        extensions = app.extensions["ia_v7"]
        return CommandService(extensions["repository"], extensions["settings"].export_dir)


def test_command_service_help(app):
    service = make_service(app)
    result = service.execute(1, "/help")
    assert result.success
    assert "/help" in result.message


def test_command_service_unknown(app):
    service = make_service(app)
    result = service.execute(1, "/inconnue")
    assert not result.success
    assert "inconnue" in result.message.lower()


def test_help_command_via_chat_route(client):
    conversation = create_conversation(client)
    response = client.post(
        f"/api/ia/conversations/{conversation['id']}/chat",
        json={"message": "/help"},
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "/help" in body
    assert '"fin": true' in body

    messages = client.get(
        f"/api/ia/conversations/{conversation['id']}/messages"
    ).get_json()
    assert messages[0]["role"] == "user"
    assert messages[0]["contenu"] == "/help"
    assert messages[1]["role"] == "assistant"
    assert "/help" in messages[1]["contenu"]


def test_unknown_command_via_chat_route_not_persisted_as_answer(client):
    conversation = create_conversation(client)
    response = client.post(
        f"/api/ia/conversations/{conversation['id']}/chat",
        json={"message": "/inconnue"},
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert '"erreur"' in body

    messages = client.get(
        f"/api/ia/conversations/{conversation['id']}/messages"
    ).get_json()
    assert [message["role"] for message in messages] == ["user"]


def test_normal_message_still_goes_through_ollama(client):
    conversation = create_conversation(client)
    response = client.post(
        f"/api/ia/conversations/{conversation['id']}/chat",
        json={"message": "Bonjour"},
    )
    body = response.get_data(as_text=True)
    assert "depuis IA V7" in body


def test_write_extracts_deliverable_block(app, tmp_path):
    service = make_service(app)
    with app.app_context():
        repository = app.extensions["ia_v7"]["repository"]
        conversation = repository.create_conversation("", "modele-test", False, None)
        repository.append_message(
            conversation["id"],
            "assistant",
            "Voici :\n```livrable\nContenu du rapport\n```\nVoila.",
        )
    result = service.execute(conversation["id"], f"/write rapport {tmp_path}")
    assert result.success
    written = tmp_path / "rapport.md"
    assert written.exists()
    assert written.read_text(encoding="utf-8") == "Contenu du rapport"


def test_write_default_export_dir(app):
    service = make_service(app)
    with app.app_context():
        repository = app.extensions["ia_v7"]["repository"]
        export_dir = app.extensions["ia_v7"]["settings"].export_dir
        conversation = repository.create_conversation("", "modele-test", False, None)
        repository.append_message(conversation["id"], "assistant", "Reponse simple")
    result = service.execute(conversation["id"], "/write reponse")
    assert result.success
    assert (export_dir / "reponse.md").exists()


def test_write_refuses_to_overwrite(app, tmp_path):
    service = make_service(app)
    existing = tmp_path / "rapport.md"
    existing.write_text("ancien contenu", encoding="utf-8")
    with app.app_context():
        repository = app.extensions["ia_v7"]["repository"]
        conversation = repository.create_conversation("", "modele-test", False, None)
        repository.append_message(conversation["id"], "assistant", "Nouveau contenu")
    result = service.execute(conversation["id"], f"/write rapport {tmp_path}")
    assert not result.success
    assert "existe déjà" in result.message
    assert existing.read_text(encoding="utf-8") == "ancien contenu"


def test_write_no_assistant_message(app):
    service = make_service(app)
    with app.app_context():
        repository = app.extensions["ia_v7"]["repository"]
        conversation = repository.create_conversation("", "modele-test", False, None)
    result = service.execute(conversation["id"], "/write rapport")
    assert not result.success
    assert "assistant" in result.message.lower()


def test_write_missing_filename(app):
    service = make_service(app)
    result = service.execute(1, "/write")
    assert not result.success


def test_rgpd_text_mode(app):
    service = make_service(app)
    text = (
        "/rgpd Contact : jean.dupont@example.com ou 06 12 34 56 78.\n"
        "Mme Durand habite 12 rue des Lilas, 75011 Paris."
    )
    result = service.execute(1, text)
    assert result.success
    assert "jean.dupont@example.com" not in result.message
    assert "06 12 34 56 78" not in result.message
    assert "Mme Durand" not in result.message
    assert "rue des Lilas" not in result.message
    assert "[DONNÉE_SENSIBLE]" in result.message


def test_rgpd_text_mode_preserves_newlines(app):
    service = make_service(app)
    result = service.execute(1, "/rgpd ligne un\nligne deux")
    assert result.success
    assert "ligne un\nligne deux" in result.message


def test_rgpd_file_mode(app, tmp_path):
    service = make_service(app)
    source = tmp_path / "clients.txt"
    source.write_text(
        "M. Martin, tel 0612345678, mail martin@societe.fr, IBAN FR7630006000011234567890189",
        encoding="utf-8",
    )
    result = service.execute(1, f"/rgpd {source}")
    assert result.success
    target = tmp_path / "clients_anonymise.md"
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "martin@societe.fr" not in content
    assert "0612345678" not in content
    assert "FR76" not in content
    assert "M. Martin" not in content
    assert "[DONNÉE_SENSIBLE]" in content


def test_rgpd_file_uppercase_command(app, tmp_path):
    service = make_service(app)
    source = tmp_path / "note.txt"
    source.write_text("mail : a@b.fr", encoding="utf-8")
    result = service.execute(1, f"/RGPD {source}")
    assert result.success
    assert (tmp_path / "note_anonymise.md").exists()


def test_rgpd_file_not_found(app, tmp_path):
    service = make_service(app)
    result = service.execute(1, f"/rgpd {tmp_path / 'absent.txt'}")
    assert not result.success
    assert "non trouvé" in result.message


def test_rgpd_refuses_overwrite(app, tmp_path):
    service = make_service(app)
    source = tmp_path / "doc.txt"
    source.write_text("mail : a@b.fr", encoding="utf-8")
    existing = tmp_path / "doc_anonymise.md"
    existing.write_text("ancien", encoding="utf-8")
    result = service.execute(1, f"/rgpd {source}")
    assert not result.success
    assert "existe déjà" in result.message
    assert existing.read_text(encoding="utf-8") == "ancien"


def test_rgpd_invalid_format(app, tmp_path):
    service = make_service(app)
    source = tmp_path / "image.bin"
    source.write_bytes(b"\xff\xfe\x00\x01\x80\x81")
    result = service.execute(1, f"/rgpd {source}")
    assert not result.success
    assert "Format invalide" in result.message


def test_rgpd_missing_args(app):
    service = make_service(app)
    result = service.execute(1, "/rgpd")
    assert not result.success
    assert "Usage" in result.message
