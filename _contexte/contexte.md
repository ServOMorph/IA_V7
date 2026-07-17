# Contexte — ia_v7

## Objectif (immuable sauf décision explicite)
Application autonome pilotant Ollama local : gestion de dossiers et conversations, historique conserve dans une base SQLite dediee, reponses en streaming (extraite du module IA de SerenIA Tech).

## Stack / contraintes techniques (stable, rarement modifié)
Python 3.11+, SQLite, Node.js 20+ et Playwright pour les tests UI, Ollama local

## État actuel (réécrit intégralement à chaque /close)
Commandes disponibles : `/help`, `/write`, `/rgpd` (anonymisation PII par regex, mode fichier ou texte).
Capture d'écran UI : bouton + overlay rectangle ajustable, PNG enregistrés dans `rapports_erreurs_manuels/` via `POST /api/ia/captures`.
Tests verts : 46 pytest, Playwright desktop + mobile.
En attente : test manuel de `/rgpd` (fichier de démo dans `tests-perso/`).

## Décisions structurantes (append only — 10 entrées max, archiver au-delà)
- 2026-07-17 : Initialisation du protocole vibecoding.
- 2026-07-17 : Ajout du système de commandes `/xxx` (parseur, registre, `/help`, `/write`) intercepté avant Ollama.
- 2026-07-17 : Roadmaps terminées archivées dans `_archives/` (avec `index.md` de suivi).
- 2026-07-17 : `/rgpd` en anonymisation regex déterministe (pas de LLM) ; noms détectés uniquement avec civilité.
- 2026-07-17 : Capture d'écran via html2canvas vendorisé (pas de getDisplayMedia) ; PNG dans `rapports_erreurs_manuels/` (`IA_V7_CAPTURES_DIR`).
