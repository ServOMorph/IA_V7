# Contexte — ia_v7

## Objectif (immuable sauf décision explicite)
Application autonome pilotant Ollama local : gestion de dossiers et conversations, historique conserve dans une base SQLite dediee, reponses en streaming (extraite du module IA de SerenIA Tech).

## Stack / contraintes techniques (stable, rarement modifié)
Python 3.11+, SQLite, Node.js 20+ et Playwright pour les tests UI, Ollama local

## État actuel (réécrit intégralement à chaque /close)
En mode Code, le LLM peut créer/écraser des fichiers : blocs ```fichier:<chemin relatif>``` dans sa réponse, écrits sous `chemin_travail` du dossier (garde anti-traversal). Non encore validé en usage réel avec `gemma4:12b`.
Commande `/controle_pc` (+ script `.claude/scripts/pc_control.ps1`) pour piloter l'UI ouverte (screenshot, clic borné, collage presse-papiers). Défaut identifié : le clic ne transfère pas le focus à Chrome (`SetForegroundWindow` manquant) ; correction en attente.
Tests verts : 73 pytest ; Playwright desktop et mobile.
En attente : tests manuels `/rgpd` et livrables, décisions RGPD ambiguës, validation réelle du bloc `fichier:`.

## Décisions structurantes (append only — 10 entrées max, archiver au-delà)
- 2026-07-17 : Le benchmark `/rgpd` devient le garde-fou de non-régression de l'anonymisation déterministe.
- 2026-07-17 : Les cas ambigus (noms sans civilité, pseudonymes, formats obfusqués ou fragmentés) restent hors du périmètre standard.
- 2026-07-17 : Le rapport manuel sur le renommage est clos : cette fonctionnalité était déjà implémentée et testée.
- 2026-07-17 : Correction d'une régression du pliage/dépliage des dossiers introduite par l'ajout du renommage par double-clic (`.ia-dossier-nom` n'avait pas d'`onclick`).
- 2026-07-19 : La consigne `livrable` utilise des retours à la ligne réels et `/help` est une modale locale non persistée.
- 2026-08-01 : `DELIVERABLE_INSTRUCTION` restreinte au déclenchement sur demande explicite (au lieu de toute reformulation/traduction/résumé).
- 2026-08-01 : Modèle par défaut changé pour `gemma4:12b`.
- 2026-08-13 : Les espaces Code sont des dossiers de travail persistants, séparés de Chat et associés à un chemin absolu existant.
- 2026-08-22 : Création de fichiers par le LLM en mode Code via convention bloc ```fichier:<chemin>``` (pas de tool calling) ; écrasement autorisé ; écriture confinée au `chemin_travail` du dossier.
- 2026-08-22 : Pilotage de l'UI via `/controle_pc` (script PowerShell `pc_control.ps1`) : fenêtre ciblée par titre (`findwindow`), bornes de clic strictes, relecture screenshot obligatoire avant chaque action.
