# Signals — ia_v7 (MAJ 2026-07-19)

## Actions ouvertes
- [P1] Test manuel de `/rgpd` dans l'app lancée (`python run.py`), sur le fichier de démo.
  fait quand: `/rgpd tests-perso/doc_test_rgpd.txt` produit `doc_test_rgpd_anonymise.md` sans PII résiduelle, et le mode texte collé affiche le texte anonymisé
  réf: tests-perso/doc_test_rgpd.txt, src/ia_v7/services/commands.py
- [P2] Vérifier l'efficacité de `DELIVERABLE_INSTRUCTION` après correction des retours à la ligne Markdown.
  fait quand: observation sur plusieurs échanges réels (reformulation, traduction, résumé) que le modèle respecte le bloc livrable sans manquement ; sinon décider d'un fallback ou post-traitement
  réf: src/ia_v7/services/chat.py (DELIVERABLE_INSTRUCTION)
- [P2] Décider des extensions `/rgpd` : chemins avec espaces, pseudonymes, noms sans civilité, PII écrites en lettres ou fragmentées.
  fait quand: périmètre standard et éventuel mode strict actés pour chaque cas ambigu
  réf: benchmarks/rapport_rgpd.md, src/ia_v7/services/commands.py

## Questions ouvertes

## Échéances

## Blocages

## Contexte chaud
- `/help` est une modale client : il ne crée ni conversation ni message, et Entrée ferme la modale en effaçant la saisie.
- `/write` exporte la dernière réponse assistant persistée ; l'aide ne peut donc plus remplacer un livrable dans ce parcours.
- `DELIVERABLE_INSTRUCTION` utilise maintenant de vrais retours à la ligne ; le respect du format reste dépendant du modèle Ollama.
- `/write` et `/rgpd` : en conversation éphémère, rien n'est persisté ; le texte collé à `/rgpd` avec PII est persisté en historique SQLite dans une conversation normale.
- Le benchmark `/rgpd` est reproductible : 21/26 cas conformes, 24/29 PII absentes littéralement et 21 cas obligatoires verrouillés.
- Les limites `/rgpd` restantes sont les noms sans civilité, pseudonymes et PII écrites en lettres ou fragmentées ; aucun NER ni mode strict n'est implémenté.
- Tests courants : 58 pytest réussis ; Playwright desktop et mobile réussis.

## Dernière session (2026-07-19)
<!-- Écrasé intégralement par /close. Synthèse < 25 lignes. -->
# Session du 2026-07-19

## Décisions prises
- `/help` devient une aide locale en modale afin de ne jamais polluer l'historique utilisé par `/write`.
- La consigne de livrable emploie des retours à la ligne Markdown réels, non les caractères littéraux `\n`.

## Livrables produits ou modifiés
- `src/ia_v7/services/chat.py`, `tests/test_chat.py` : correction et test de la consigne `livrable`.
- `templates/index.html`, `static/css/styles.css`, `static/js/app.js` : modale `/help` et interception avant envoi.
- `tests-ui/ui.spec.js`, `tests/test_ui_contract.py` : régression UI couverte.

## Hypothèses validées / invalidées
- VALIDE : le fichier exporté était l'aide car `/help` était la dernière réponse assistant persistée.
- VALIDE : `\n` littéraux empêchaient le parseur Markdown de reconnaître le langage `livrable`.
- EN ATTENTE : respect du format par le modèle Ollama sur plusieurs échanges réels ; test manuel `/rgpd`.

## Prochaine étape exacte
Lancer `python run.py`, tester `/help` puis `/write` après un livrable, et exécuter le scénario manuel `/rgpd`.

## Question bloquante pour la session suivante
Aucune
