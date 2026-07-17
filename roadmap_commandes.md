# Roadmap — Système de commandes chat

Objectif : permettre à l'utilisateur de taper des commandes `/xxx` dans le chat,
interceptées par le serveur au lieu d'être envoyées à Ollama. Première commande :
`/write <nom_fichier> [<path>]` qui enregistre le dernier livrable produit
(bloc ```livrable du dernier message assistant, sinon le message entier) dans un fichier.

## Phase 1 — Cœur du système de commandes [FAIT]

- Créer `src/ia_v7/services/commands.py` : parseur (message commençant par `/`),
  registre de commandes (nom → handler), résultat structuré (succès/erreur + message).
- Intercepter dans la route chat ([routes.py:249](src/ia_v7/web/routes.py#L249)) :
  si le message est une commande, exécuter le handler et renvoyer le résultat dans le
  même format SSE que le streaming Ollama (aucun appel modèle).
- Persister la commande et son résultat dans l'historique de la conversation
  (sauf conversation éphémère), comme un échange normal.
- Commande `/help` incluse d'office : liste les commandes disponibles.
- Commande inconnue → message d'erreur clair, pas d'envoi à Ollama.
- Tests : parseur, commande inconnue, `/help`, non-interception des messages normaux.

**⏸ Checkpoint** — Demander à l'utilisateur de faire `/compact` avant de continuer.
Attendre sa réponse écrite. Ne pas commencer la phase suivante sans confirmation.

## Phase 2 — Commande /write [FAIT]

- Syntaxe : `/write <nom_fichier> [<path>]`, arguments séparés par des espaces
  (path avec espaces → entre guillemets). Path absent → répertoire d'export par
  défaut défini dans la config (`IA_V7_EXPORT_DIR`, `.env.example` mis à jour).
- Source du contenu : dernier bloc ```livrable``` du dernier message assistant de la
  conversation ; à défaut, dernier message assistant complet ; aucun message → erreur.
- Écriture : création des dossiers intermédiaires, refus d'écraser un fichier existant
  sauf option explicite, extension `.md` ajoutée si absente.
- Retour utilisateur : chemin complet du fichier écrit, ou erreur explicite.
- Tests : extraction livrable, path par défaut, path fourni, fichier existant,
  conversation vide.

**⏸ Checkpoint** — Demander à l'utilisateur de faire `/compact` avant de continuer.
Attendre sa réponse écrite. Ne pas commencer la phase suivante sans confirmation.

## Phase 3 — Intégration UI [FAIT]

- `static/js/app.js` : affichage distinct des résultats de commande (pas de rendu
  "réponse modèle"), état visuel succès/erreur.
- Suggestion des commandes disponibles quand l'utilisateur tape `/` en début de champ.
- Tests Playwright : exécution de `/help` et `/write` depuis l'UI, affichage du résultat.

**⏸ Checkpoint** — Demander à l'utilisateur de faire `/compact` avant de continuer.
Attendre sa réponse écrite. Ne pas commencer la phase suivante sans confirmation.
