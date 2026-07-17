## v1.0 — 2026-07-17

### Ajouté
- Système de commandes `/xxx` intercepté côté serveur avant Ollama (`src/ia_v7/services/commands.py`).
- Commande `/help` : liste les commandes disponibles.
- Commande `/write <nom_fichier> [<path>]` : enregistre le dernier livrable de la conversation dans un fichier (`IA_V7_EXPORT_DIR` configurable).
- Endpoint `GET /api/ia/commandes`.
- Intégration UI : rendu distinct des résultats de commande (succès/erreur), autocomplétion `/` dans le champ de saisie.
- Couverture de tests complète (pytest backend, Playwright UI).
