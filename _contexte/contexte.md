# Contexte — ia_v7

## Objectif (immuable sauf décision explicite)
Application autonome pilotant Ollama local : gestion de dossiers et conversations, historique conserve dans une base SQLite dediee, reponses en streaming (extraite du module IA de SerenIA Tech).

## Stack / contraintes techniques (stable, rarement modifié)
Python 3.11+, SQLite, Node.js 20+ et Playwright pour les tests UI, Ollama local

## État actuel (réécrit intégralement à chaque /close)
Commandes disponibles : `/help`, `/write`, `/rgpd` ; `/help` est une modale locale sans persistance dans la conversation.
L'anonymisation PII fonctionne en mode fichier ou texte ; le benchmark repose sur 26 cas synthétiques, dont 21 cas obligatoires verrouillés.
Les dossiers et conversations se renomment par double-clic ; le pliage/dépliage au clic simple a été validé manuellement.
`DELIVERABLE_INSTRUCTION` emploie de vrais retours à la ligne Markdown ; le respect du bloc reste à confirmer sur des échanges Ollama réels.
Tests verts : 58 pytest ; Playwright desktop et mobile. En attente : test manuel `/rgpd` et décisions sur les cas RGPD ambigus.

## Décisions structurantes (append only — 10 entrées max, archiver au-delà)
- 2026-07-17 : Ajout du système de commandes `/xxx` (parseur, registre, `/help`, `/write`) intercepté avant Ollama.
- 2026-07-17 : Roadmaps terminées archivées dans `_archives/` (avec `index.md` de suivi).
- 2026-07-17 : `/rgpd` en anonymisation regex déterministe (pas de LLM) ; noms détectés uniquement avec civilité.
- 2026-07-17 : Capture d'écran via html2canvas vendorisé (pas de getDisplayMedia) ; PNG dans `rapports_erreurs_manuels/` (`IA_V7_CAPTURES_DIR`).
- 2026-07-17 : `DELIVERABLE_INSTRUCTION` reformulée de façon plus impérative suite à un manquement du modèle ; fallback client-side écarté pour l'instant.
- 2026-07-17 : Le benchmark `/rgpd` devient le garde-fou de non-régression de l'anonymisation déterministe.
- 2026-07-17 : Les cas ambigus (noms sans civilité, pseudonymes, formats obfusqués ou fragmentés) restent hors du périmètre standard.
- 2026-07-17 : Le rapport manuel sur le renommage est clos : cette fonctionnalité était déjà implémentée et testée.
- 2026-07-17 : Correction d'une régression du pliage/dépliage des dossiers introduite par l'ajout du renommage par double-clic (`.ia-dossier-nom` n'avait pas d'`onclick`).
- 2026-07-19 : La consigne `livrable` utilise des retours à la ligne réels et `/help` est une modale locale non persistée.
