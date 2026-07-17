from __future__ import annotations

import argparse

from .app import create_app
from .config import Settings


def parse_args() -> argparse.Namespace:
    defaults = Settings.from_env()
    parser = argparse.ArgumentParser(description="Lance IA V7 en local.")
    parser.add_argument("--host", default=defaults.host, help="Adresse d'écoute.")
    parser.add_argument("--port", default=defaults.port, type=int, help="Port d'écoute.")
    parser.add_argument("--debug", action="store_true", help="Active le mode debug Flask.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(host=args.host, port=args.port)
    app = create_app(settings=settings)
    url = f"http://{settings.host}:{settings.port}"
    print(f"IA V7 disponible sur {url}")
    print("Arrêt du serveur : Ctrl+C")
    app.run(
        host=settings.host,
        port=settings.port,
        debug=args.debug,
        threaded=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()

