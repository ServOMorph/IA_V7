# Contexte — ia_v7

## Objectif (immuable sauf décision explicite)
Application autonome pilotant Ollama local : gestion de dossiers et conversations, historique conserve dans une base SQLite dediee, reponses en streaming (extraite du module IA de SerenIA Tech).

## Stack / contraintes techniques (stable, rarement modifié)
Python 3.11+, SQLite, Node.js 20+ et Playwright pour les tests UI, Ollama local

## État actuel (réécrit intégralement à chaque /close)
Système de commandes `/xxx` intercepté côté serveur, livré et testé (backend + UI). Commandes disponibles : `/help`, `/write <nom_fichier> [<path>]`. Roadmap `roadmap_commandes.md` entièrement [FAIT].

## Décisions structurantes (append only — 10 entrées max, archiver au-delà)
- 2026-07-17 : Initialisation du protocole vibecoding.
- 2026-07-17 : Ajout du système de commandes `/xxx` (parseur, registre, `/help`, `/write`) intercepté avant Ollama.
