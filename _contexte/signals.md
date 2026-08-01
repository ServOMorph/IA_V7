# Signals — ia_v7 (MAJ 2026-08-01)

## Actions ouvertes
- [P1] Test manuel de `/rgpd` dans l'app lancée (`python run.py`), sur le fichier de démo.
  fait quand: `/rgpd tests-perso/doc_test_rgpd.txt` produit `doc_test_rgpd_anonymise.md` sans PII résiduelle, et le mode texte collé affiche le texte anonymisé
  réf: tests-perso/doc_test_rgpd.txt, src/ia_v7/services/commands.py
- [P1] Vérifier en usage réel que `DELIVERABLE_INSTRUCTION` restreinte ne déclenche plus le bloc ```livrable``` en conversation normale.
  fait quand: observation sur plusieurs échanges réels (reformulation, traduction, résumé sans demande explicite) que les réponses restent en texte libre, et que le bloc apparaît bien quand un livrable est demandé explicitement
  réf: src/ia_v7/services/chat.py (DELIVERABLE_INSTRUCTION)
- [P2] Décider des extensions `/rgpd` : chemins avec espaces, pseudonymes, noms sans civilité, PII écrites en lettres ou fragmentées.
  fait quand: périmètre standard et éventuel mode strict actés pour chaque cas ambigu
  réf: benchmarks/rapport_rgpd.md, src/ia_v7/services/commands.py

## Contexte chaud
- `DELIVERABLE_INSTRUCTION` ne se déclenche plus que sur demande explicite (mots-clés "livrable", "à copier-coller", "document/texte final") ; hors de ces cas, réponse en texte normal.
- Modèle par défaut : `gemma4:12b` (config.py, data/default_model.txt, .tmp_ui_data/default_model.txt — ces deux derniers gitignorés).
- `/help` est une modale client : il ne crée ni conversation ni message, et Entrée ferme la modale en effaçant la saisie.
- `/write` exporte la dernière réponse assistant persistée ; l'aide ne peut donc plus remplacer un livrable dans ce parcours.
- `/write` et `/rgpd` : en conversation éphémère, rien n'est persisté ; le texte collé à `/rgpd` avec PII est persisté en historique SQLite dans une conversation normale.
- Le benchmark `/rgpd` est reproductible : 21/26 cas conformes, 24/29 PII absentes littéralement et 21 cas obligatoires verrouillés.
- Les limites `/rgpd` restantes sont les noms sans civilité, pseudonymes et PII écrites en lettres ou fragmentées ; aucun NER ni mode strict n'est implémenté.
- Tests courants : test_chat.py vert après restriction de la consigne livrable ; 58 pytest et Playwright non relancés en intégralité cette session.

## Dernière session (2026-08-01)
<!-- Écrasé intégralement par /close. Synthèse < 25 lignes. -->
# Session du 2026-08-01

## Décisions prises
- Modèle par défaut changé pour `gemma4:12b` (tag confirmé explicitement par l'utilisateur malgré absence du catalogue Ollama connu).
- `DELIVERABLE_INSTRUCTION` restreinte : le bloc ```livrable``` ne se déclenche plus que sur demande explicite, plus sur simple reformulation/traduction/résumé.

## Livrables produits ou modifiés
- `src/ia_v7/config.py` : fallback `default_model` = `gemma4:12b`.
- `data/default_model.txt`, `.tmp_ui_data/default_model.txt` : alignés sur `gemma4:12b` (fichiers gitignorés).
- `src/ia_v7/services/chat.py` : `DELIVERABLE_INSTRUCTION` reformulée.
- `README.md`, `CHANGELOG.md` (v2.1) : mis à jour.

## Hypothèses validées / invalidées
- VALIDE : `tests/test_chat.py` reste vert après la reformulation de la consigne (format `livrable\n...\n` inchangé).
- EN ATTENTE : confirmation en usage réel que la restriction élimine bien le sur-déclenchement du bloc livrable.

## Prochaine étape exacte
Lancer `python run.py`, observer plusieurs échanges réels (avec et sans demande explicite de livrable) et le scénario manuel `/rgpd`.

## Question bloquante pour la session suivante
Aucune
