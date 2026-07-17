## v1.4 — 2026-07-17

### Modifié
- Rapport d'erreur manuel traité et supprimé de `rapports_erreurs_manuels/`.
- Planification d'un benchmark automatisé pour `/rgpd` (corpus de difficulté croissante, rapport lisible + pistes d'amélioration) ; contexte détaillé consigné dans `_contexte/signals.md`, à démarrer en priorité session suivante.

## v1.3 — 2026-07-17

### Modifié
- Consigne système `DELIVERABLE_INSTRUCTION` reformulée de façon plus impérative (bloc ```livrable``` obligatoire pour tout texte réutilisable), suite à un manquement observé du modèle Ollama lors d'une reformulation.

## v1.2 — 2026-07-17

### Ajouté
- Commande `/rgpd <chemin_fichier | texte>` : anonymisation des PII par regex (emails, téléphones, NIR, IBAN, CB, IP, adresses postales, noms avec civilité) ; mode fichier écrit `<original>_anonymise.md`, mode texte affiche le résultat.
- Capture d'écran depuis l'UI : bouton « Capture », overlay de sélection rectangulaire ajustable (déplacement + 8 poignées), enregistrement PNG horodaté dans `rapports_erreurs_manuels/` via `POST /api/ia/captures` (`IA_V7_CAPTURES_DIR`).
- `html2canvas` vendorisé dans `static/vendor/`.
- Fichier de démo PII fictives `tests-perso/doc_test_rgpd.txt`.
- `/start` signale les fichiers en attente dans `rapports_erreurs_manuels/` sans les lire.

### Modifié
- `CommandContext` transporte le texte brut du message (préservation des sauts de ligne pour `/rgpd`).
- `MAX_CONTENT_LENGTH` porté de 1 Mo à 10 Mo.

## v1.1 — 2026-07-17

### Modifié
- Roadmaps terminées désormais archivées dans `_archives/` avec un index de suivi (`_archives/index.md`).

## v1.0 — 2026-07-17

### Ajouté
- Système de commandes `/xxx` intercepté côté serveur avant Ollama (`src/ia_v7/services/commands.py`).
- Commande `/help` : liste les commandes disponibles.
- Commande `/write <nom_fichier> [<path>]` : enregistre le dernier livrable de la conversation dans un fichier (`IA_V7_EXPORT_DIR` configurable).
- Endpoint `GET /api/ia/commandes`.
- Intégration UI : rendu distinct des résultats de commande (succès/erreur), autocomplétion `/` dans le champ de saisie.
- Couverture de tests complète (pytest backend, Playwright UI).
