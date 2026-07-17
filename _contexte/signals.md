# Signals — ia_v7   (MAJ 2026-07-17)

## Actions ouvertes

## Questions ouvertes

## Échéances

## Blocages

## Contexte chaud
- Système de commandes `/xxx` opérationnel (`/help`, `/write`) : interception serveur avant Ollama.
- `/write` nécessite un message assistant déjà persisté dans la conversation ; en mode éphémère,
  rien n'est jamais persisté donc `/write` échouera systématiquement (comportement voulu, pas un bug).

## Dernière session (2026-07-17)
<!-- Écrasé intégralement par /close. Synthèse < 25 lignes. -->
# Session du 2026-07-17

## Décisions prises
- Système de commandes `/xxx` livré en 3 phases (parseur/registre, `/write`, intégration UI), toutes [FAIT].
- Statuts de roadmap marqués [FAIT] en cours de session (dérogation explicite de l'utilisateur à la règle générale).

## Livrables produits ou modifiés
- src/ia_v7/services/commands.py : créé (parseur, registre, `/help`, `/write`)
- src/ia_v7/config.py, .env.example, src/ia_v7/app.py : IA_V7_EXPORT_DIR ajouté
- src/ia_v7/web/routes.py : endpoint GET /api/ia/commandes ajouté
- static/js/app.js, static/css/styles.css, templates/index.html : rendu distinct des commandes + autocomplétion `/`
- tests/test_commands.py, tests/conftest.py, tests-ui/ui.spec.js, scripts/run_ui_test_server.py : couverture complète
- roadmap_commandes.md : 3 phases [FAIT]

## Hypothèses validées / invalidées
- VALIDE : `shlex.split(..., posix=False)` requis pour préserver les chemins Windows.
- VALIDE : en usage réel, l'erreur `/write` "Aucun message assistant" venait du mode éphémère (confirmé par l'utilisateur).

## Prochaine étape exacte
Aucune tâche ouverte sur ce sujet. Reprendre au prochain besoin fonctionnel.

## Question bloquante pour la session suivante
Aucune.
