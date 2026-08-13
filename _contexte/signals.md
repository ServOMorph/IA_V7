# Signals — ia_v7 (MAJ 2026-08-13)

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
- Mode Code : les dossiers de travail possèdent un chemin absolu existant, les dossiers Chat et Code sont isolés et le mode est visible dans le header.
- Tests courants : 63 pytest et Playwright desktop/mobile verts après l’ajout du mode Code.

## Dernière session (2026-08-13)
<!-- Écrasé intégralement par /close. Synthèse < 25 lignes. -->
# Session du 2026-08-13

## Décisions prises
- Le mode Code réutilise l’écran d’agent existant, avec dossiers de travail séparés du mode Chat.
- Un dossier Code requiert un chemin absolu vers un dossier existant.

## Livrables produits ou modifiés
- API et SQLite : modes de dossier et chemins de travail persistants, avec migration des bases existantes.
- Interface : bascule Chat/Code, couleur spécifique, modale de création de dossier et affichage du chemin.
- Tests API, SQLite et Playwright : ajoutés et exécutés.

## Hypothèses validées / invalidées
- VALIDE : les dossiers Code sont isolés de la liste Chat ; une conversation persistante reste visible après rechargement, une éphémère non.

## Prochaine étape exacte
Lancer `python run.py` et exécuter les scénarios manuels `/rgpd` et de demande explicite de livrable.

## Question bloquante pour la session suivante
Aucune
