from __future__ import annotations

from flask import Flask

from .config import Settings
from .infrastructure.database import Database
from .infrastructure.ollama import OllamaClient
from .infrastructure.repository import IaRepository
from .services.chat import ChatService
from .services.commands import CommandService
from .services.context import FactExtractor
from .web.routes import api_bp, web_bp


def create_app(
    settings: Settings | None = None,
    ollama_client: object | None = None,
) -> Flask:
    settings = settings or Settings.from_env()
    app = Flask(
        __name__,
        static_folder=str(settings.project_root / "static"),
        template_folder=str(settings.project_root / "templates"),
    )
    app.config.update(JSON_AS_ASCII=False, MAX_CONTENT_LENGTH=1024 * 1024)

    database = Database(settings.database_path)
    database.initialize()
    repository = IaRepository(database)
    ollama = ollama_client or OllamaClient(
        base_url=settings.ollama_url,
        default_model_path=settings.default_model_path,
        fallback_model=settings.default_model,
        num_ctx=settings.num_ctx,
    )
    fact_extractor = FactExtractor(repository, ollama)
    chat_service = ChatService(
        repository=repository,
        ollama=ollama,
        fact_extractor=fact_extractor,
        num_ctx=settings.num_ctx,
    )
    command_service = CommandService(repository=repository, export_dir=settings.export_dir)

    app.extensions["ia_v7"] = {
        "settings": settings,
        "database": database,
        "repository": repository,
        "ollama": ollama,
        "fact_extractor": fact_extractor,
        "chat_service": chat_service,
        "command_service": command_service,
    }
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    return app

