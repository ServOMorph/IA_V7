# Migration depuis SérénIA Tech

Date : 2026-07-17

## Source protégée

`C:\Users\raph6\Documents\SerenIATech\SérénIATech_dev\UI`

La source a été inspectée et lue sans écriture. Le standalone a été construit uniquement dans `D:\ServOMorph\IA_V7`.

## Périmètre extrait

- interface HTML du panneau IA ;
- styles et variables graphiques SérénIA Tech ;
- comportement `js/ia.js` ;
- routes `/api/ia/*` ;
- pilotage d’Ollama ;
- fenêtre de contexte et extraction de faits ;
- tables `ia_dossiers`, `ia_conversations`, `ia_messages`, `ia_faits`.

Les modules métier sans lien avec l’IA et leurs dépendances ne sont pas copiés.

## Données importées

| Table | Source | Cible | Écart |
|---|---:|---:|---:|
| `ia_dossiers` | 1 | 1 | 0 |
| `ia_conversations` | 38 | 38 | 0 |
| `ia_messages` | 13 | 12 | 1 |
| `ia_faits` | 22 | 22 | 0 |

Le message `ia_messages.id = 60` référençait la conversation inexistante `35`. Il était donc inaccessible dans l’application historique. La migration stricte a d’abord échoué, puis cette unique ligne a été explicitement exclue avec `--skip-orphans`. La base cible passe `PRAGMA integrity_check` et `PRAGMA foreign_key_check`.

## Écarts structurants

- base SQLite propre au module au lieu de la base monolithique ;
- chemins et modèle par défaut configurables, sans dépendance absolue ;
- fabrique d’application et injection du client Ollama ;
- séparation routes, services, persistance et infrastructure ;
- validation des relations SQLite activée sur chaque connexion ;
- rendu Markdown assaini avec DOMPurify ;
- comportement responsive ajouté sans modifier les couleurs ni typographies de référence.

