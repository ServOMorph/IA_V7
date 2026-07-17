from __future__ import annotations

import sqlite3
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, render_template, request

from ia_v7.services.commands import is_command


web_bp = Blueprint("web", __name__)
api_bp = Blueprint("ia_api", __name__, url_prefix="/api/ia")


def services() -> dict[str, Any]:
    return current_app.extensions["ia_v7"]


def payload() -> dict[str, Any]:
    return request.get_json(silent=True) or {}


@web_bp.get("/")
def index() -> str:
    return render_template("index.html")


@api_bp.get("/sante")
def health() -> tuple[Response, int] | Response:
    repository = services()["repository"]
    try:
        repository.list_folders()
    except sqlite3.Error as error:
        return jsonify({"ok": False, "error": str(error)}), 503
    return jsonify({"ok": True})


@api_bp.get("/dossiers")
def list_folders() -> Response:
    return jsonify(services()["repository"].list_folders())


@api_bp.post("/dossiers")
def create_folder() -> tuple[Response, int]:
    data = payload()
    name = str(data.get("nom") or "").strip()
    if not name:
        return jsonify({"error": "Le nom est requis"}), 400
    folder = services()["repository"].create_folder(
        name, str(data.get("system_prompt") or "")
    )
    return jsonify(folder), 201


@api_bp.put("/dossiers/<int:folder_id>")
def update_folder(folder_id: int) -> tuple[Response, int] | Response:
    data = payload()
    fields: dict[str, Any] = {}
    if "nom" in data:
        name = str(data.get("nom") or "").strip()
        if not name:
            return jsonify({"error": "Le nom ne peut pas être vide"}), 400
        fields["nom"] = name
    if "system_prompt" in data:
        fields["system_prompt"] = str(data.get("system_prompt") or "")
    if not fields:
        return jsonify({"error": "Aucun champ à modifier"}), 400
    folder = services()["repository"].update_folder(folder_id, fields)
    if folder is None:
        return jsonify({"error": "Dossier introuvable"}), 404
    return jsonify(folder)


@api_bp.delete("/dossiers/<int:folder_id>")
def delete_folder(folder_id: int) -> tuple[Response, int] | Response:
    if not services()["repository"].delete_folder(folder_id):
        return jsonify({"error": "Dossier introuvable"}), 404
    return jsonify({"success": True})


@api_bp.get("/conversations")
def list_conversations() -> tuple[Response, int] | Response:
    raw_folder_id = request.args.get("dossier_id")
    if raw_folder_id in (None, ""):
        folder_id = None
    else:
        try:
            folder_id = int(raw_folder_id)
        except ValueError:
            return jsonify({"error": "Identifiant de dossier invalide"}), 400
    return jsonify(services()["repository"].list_conversations(folder_id))


@api_bp.get("/conversations/<int:conversation_id>")
def get_conversation(conversation_id: int) -> tuple[Response, int] | Response:
    conversation = services()["repository"].get_conversation(
        conversation_id, include_messages=True
    )
    if conversation is None:
        return jsonify({"error": "Conversation introuvable"}), 404
    return jsonify(conversation)


@api_bp.post("/conversations")
def create_conversation() -> tuple[Response, int]:
    data = payload()
    model = str(data.get("modele") or "").strip()
    if not model:
        model = services()["ollama"].get_default_model()
    folder_id = data.get("dossier_id")
    if folder_id is not None:
        try:
            folder_id = int(folder_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Identifiant de dossier invalide"}), 400
    try:
        conversation = services()["repository"].create_conversation(
            title=str(data.get("titre") or "").strip(),
            model=model,
            ephemeral=bool(data.get("ephemere")),
            folder_id=folder_id,
        )
    except sqlite3.IntegrityError:
        return jsonify({"error": "Dossier introuvable"}), 400
    return jsonify(conversation), 201


@api_bp.put("/conversations/<int:conversation_id>")
def update_conversation(conversation_id: int) -> tuple[Response, int] | Response:
    data = payload()
    fields: dict[str, Any] = {}
    if "titre" in data:
        fields["titre"] = str(data.get("titre") or "").strip()
    if "modele" in data:
        fields["modele"] = str(data.get("modele") or "").strip()
    if "dossier_id" in data:
        folder_id = data.get("dossier_id")
        if folder_id is not None:
            try:
                folder_id = int(folder_id)
            except (TypeError, ValueError):
                return jsonify({"error": "Identifiant de dossier invalide"}), 400
        fields["dossier_id"] = folder_id
    if not fields:
        return jsonify({"error": "Aucun champ à modifier"}), 400
    try:
        conversation = services()["repository"].update_conversation(
            conversation_id, fields
        )
    except sqlite3.IntegrityError:
        return jsonify({"error": "Dossier introuvable"}), 400
    if conversation is None:
        return jsonify({"error": "Conversation introuvable"}), 404
    return jsonify(conversation)


@api_bp.delete("/conversations/<int:conversation_id>")
def delete_conversation(conversation_id: int) -> tuple[Response, int] | Response:
    if not services()["repository"].delete_conversation(conversation_id):
        return jsonify({"error": "Conversation introuvable"}), 404
    return jsonify({"success": True})


@api_bp.get("/conversations/<int:conversation_id>/messages")
def list_messages(conversation_id: int) -> Response:
    return jsonify(services()["repository"].list_messages(conversation_id))


@api_bp.get("/commandes")
def list_commands() -> Response:
    registry = services()["command_service"].registry
    return jsonify(
        [
            {"nom": command.name, "description": command.description}
            for command in registry.list_commands()
        ]
    )


@api_bp.get("/modeles")
def list_models() -> tuple[Response, int] | Response:
    status = services()["ollama"].status()
    if not status.get("actif"):
        return jsonify({"error": "Ollama injoignable", "modeles": []}), 503
    return jsonify({"modeles": status.get("modeles", [])})


@api_bp.get("/statut")
def ollama_status() -> Response:
    ollama = services()["ollama"]
    active = ollama.is_server_active()
    loaded = ollama.loaded_models() if active else []
    return jsonify(
        {
            "serveur": active,
            "modeles_charges": [model.get("name") for model in loaded if model.get("name")],
        }
    )


@api_bp.post("/serveur/start")
def start_server() -> tuple[Response, int] | Response:
    try:
        services()["ollama"].start_server()
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    return jsonify({"success": True})


@api_bp.post("/serveur/stop")
def stop_server() -> tuple[Response, int] | Response:
    try:
        services()["ollama"].stop_server()
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    return jsonify({"success": True})


def requested_model() -> tuple[str | None, tuple[Response, int] | None]:
    model = str(payload().get("modele") or "").strip()
    if not model:
        return None, (jsonify({"error": "Modèle requis"}), 400)
    return model, None


@api_bp.post("/modele/charger")
def load_model() -> tuple[Response, int] | Response:
    model, error = requested_model()
    if error:
        return error
    try:
        services()["ollama"].load_model(model)
    except Exception as exception:
        return jsonify({"error": str(exception)}), 500
    return jsonify({"success": True})


@api_bp.post("/modele/decharger")
def unload_model() -> tuple[Response, int] | Response:
    model, error = requested_model()
    if error:
        return error
    try:
        services()["ollama"].unload_model(model)
    except Exception as exception:
        return jsonify({"error": str(exception)}), 500
    return jsonify({"success": True})


@api_bp.post("/modele/defaut")
def set_default_model() -> tuple[Response, int] | Response:
    model, error = requested_model()
    if error:
        return error
    try:
        services()["ollama"].set_default_model(model)
    except OSError as exception:
        return jsonify({"error": str(exception)}), 500
    return jsonify({"success": True, "modele": model})


@api_bp.post("/conversations/<int:conversation_id>/chat")
def chat(conversation_id: int) -> tuple[Response, int] | Response:
    message = str(payload().get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message vide"}), 400
    if services()["repository"].get_conversation(conversation_id) is None:
        return jsonify({"error": "Conversation introuvable"}), 404
    if is_command(message):
        stream = services()["command_service"].stream_execute(conversation_id, message)
    else:
        stream = services()["chat_service"].stream_chat(conversation_id, message)
    response = Response(stream, mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@api_bp.post("/conversations/<int:conversation_id>/titre-auto")
def auto_title(conversation_id: int) -> tuple[Response, int] | Response:
    try:
        title = services()["chat_service"].generate_title(conversation_id)
    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        return jsonify({"error": str(error)}), 500
    return jsonify({"titre": title})

