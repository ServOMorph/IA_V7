from __future__ import annotations


def create_conversation(client, **data):
    response = client.post("/api/ia/conversations", json=data)
    assert response.status_code == 201
    return response.get_json()


def test_index_and_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "SérénIA Tech" in response.get_data(as_text=True)
    assert client.get("/api/ia/sante").get_json() == {"ok": True}


def test_folder_crud(client):
    assert client.get("/api/ia/dossiers").get_json() == []
    response = client.post(
        "/api/ia/dossiers", json={"nom": "Projet", "system_prompt": "Sois bref"}
    )
    assert response.status_code == 201
    folder = response.get_json()
    assert folder["nom"] == "Projet"

    response = client.put(
        f"/api/ia/dossiers/{folder['id']}",
        json={"nom": "Projet renommé", "system_prompt": "Sois précis"},
    )
    assert response.get_json()["nom"] == "Projet renommé"
    assert client.delete(f"/api/ia/dossiers/{folder['id']}").get_json() == {"success": True}
    assert client.delete(f"/api/ia/dossiers/{folder['id']}").status_code == 404


def test_folder_validation(client):
    assert client.post("/api/ia/dossiers", json={"nom": " "}).status_code == 400
    assert client.put("/api/ia/dossiers/999", json={}).status_code == 400
    assert client.put("/api/ia/dossiers/999", json={"nom": "Valide"}).status_code == 404


def test_conversation_crud_and_filter(client):
    folder = client.post("/api/ia/dossiers", json={"nom": "Dossier"}).get_json()
    conversation = create_conversation(client, dossier_id=folder["id"], titre="Initiale")
    assert conversation["modele"] == "modele-test:latest"

    listed = client.get(f"/api/ia/conversations?dossier_id={folder['id']}").get_json()
    assert [item["id"] for item in listed] == [conversation["id"]]

    updated = client.put(
        f"/api/ia/conversations/{conversation['id']}",
        json={"titre": "Renommée", "modele": "autre:1b"},
    ).get_json()
    assert updated["titre"] == "Renommée"
    assert updated["modele"] == "autre:1b"

    detail = client.get(f"/api/ia/conversations/{conversation['id']}").get_json()
    assert detail["messages"] == []
    assert client.delete(f"/api/ia/conversations/{conversation['id']}").status_code == 200
    assert client.get(f"/api/ia/conversations/{conversation['id']}").status_code == 404


def test_conversation_validation(client):
    assert client.get("/api/ia/conversations?dossier_id=abc").status_code == 400
    assert client.post("/api/ia/conversations", json={"dossier_id": "abc"}).status_code == 400
    assert client.post("/api/ia/conversations", json={"dossier_id": 999}).status_code == 400
    assert client.put("/api/ia/conversations/999", json={}).status_code == 400
    assert client.put("/api/ia/conversations/999", json={"titre": "X"}).status_code == 404


def test_folder_delete_cascades_conversations(client):
    folder = client.post("/api/ia/dossiers", json={"nom": "À supprimer"}).get_json()
    conversation = create_conversation(client, dossier_id=folder["id"])
    client.delete(f"/api/ia/dossiers/{folder['id']}")
    assert client.get(f"/api/ia/conversations/{conversation['id']}").status_code == 404


def test_persistent_streaming_chat_and_title(client, fake_ollama):
    conversation = create_conversation(client, modele="modele-test:latest")
    response = client.post(
        f"/api/ia/conversations/{conversation['id']}/chat",
        json={"message": "Bonjour"},
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert "Bonjour " in body
    assert "depuis IA V7" in body
    assert '"fin": true' in body

    messages = client.get(
        f"/api/ia/conversations/{conversation['id']}/messages"
    ).get_json()
    assert [(message["role"], message["contenu"]) for message in messages] == [
        ("user", "Bonjour"),
        ("assistant", "Bonjour depuis IA V7"),
    ]

    response = client.post(f"/api/ia/conversations/{conversation['id']}/titre-auto")
    assert response.get_json() == {"titre": "Titre de test"}


def test_ephemeral_chat_is_not_persisted(client):
    conversation = create_conversation(client, ephemere=True)
    client.post(
        f"/api/ia/conversations/{conversation['id']}/chat",
        json={"message": "Secret temporaire"},
    ).get_data()
    assert client.get(
        f"/api/ia/conversations/{conversation['id']}/messages"
    ).get_json() == []
    assert client.post(f"/api/ia/conversations/{conversation['id']}/titre-auto").status_code == 400


def test_chat_validation(client):
    conversation = create_conversation(client)
    assert client.post(
        f"/api/ia/conversations/{conversation['id']}/chat", json={"message": " "}
    ).status_code == 400
    assert client.post("/api/ia/conversations/999/chat", json={"message": "Bonjour"}).status_code == 404
    assert client.post("/api/ia/conversations/999/titre-auto").status_code == 404


def test_ollama_endpoints(client, fake_ollama):
    assert client.get("/api/ia/modeles").get_json()["modeles"] == fake_ollama.models
    status = client.get("/api/ia/statut").get_json()
    assert status == {"serveur": True, "modeles_charges": ["modele-test:latest"]}

    assert client.post("/api/ia/modele/charger", json={}).status_code == 400
    assert client.post("/api/ia/modele/charger", json={"modele": "autre:1b"}).status_code == 200
    assert fake_ollama.loaded_requests == ["autre:1b"]
    assert client.post("/api/ia/modele/decharger", json={"modele": "autre:1b"}).status_code == 200
    assert fake_ollama.unloaded_requests == ["autre:1b"]

    assert client.post("/api/ia/modele/defaut", json={"modele": "autre:1b"}).status_code == 200
    assert fake_ollama.model_file.read_text(encoding="utf-8") == "autre:1b"

    client.post("/api/ia/serveur/stop")
    assert fake_ollama.stopped is True
    assert client.get("/api/ia/modeles").status_code == 503
    client.post("/api/ia/serveur/start")
    assert fake_ollama.started is True



PNG_1X1 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_capture_saves_png(client, app):
    response = client.post("/api/ia/captures", json={"image": PNG_1X1})
    assert response.status_code == 201
    filename = response.get_json()["fichier"]
    assert filename.startswith("capture_") and filename.endswith(".png")
    captures_dir = app.extensions["ia_v7"]["settings"].captures_dir
    saved = captures_dir / filename
    assert saved.exists()
    assert saved.read_bytes().startswith(b"\x89PNG")


def test_capture_unique_filenames(client, app):
    first = client.post("/api/ia/captures", json={"image": PNG_1X1})
    second = client.post("/api/ia/captures", json={"image": PNG_1X1})
    assert first.status_code == 201 and second.status_code == 201
    assert first.get_json()["fichier"] != second.get_json()["fichier"]


def test_capture_rejects_missing_image(client):
    assert client.post("/api/ia/captures", json={}).status_code == 400


def test_capture_rejects_non_data_url(client):
    response = client.post("/api/ia/captures", json={"image": "pas une image"})
    assert response.status_code == 400


def test_capture_rejects_invalid_base64(client):
    response = client.post(
        "/api/ia/captures", json={"image": "data:image/png;base64,%%%invalide%%%"}
    )
    assert response.status_code == 400


def test_capture_rejects_non_png_content(client):
    import base64

    fake = "data:image/png;base64," + base64.b64encode(b"GIF89a contenu").decode()
    response = client.post("/api/ia/captures", json={"image": fake})
    assert response.status_code == 400
    assert "PNG" in response.get_json()["error"]
