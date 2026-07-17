# Signals — ia_v7   (MAJ 2026-07-17)

## Actions ouvertes
- [P1] Test manuel de `/rgpd` dans l'app lancée (`python run.py`), sur le fichier de démo.
  fait quand: `/rgpd tests-perso/doc_test_rgpd.txt` produit `doc_test_rgpd_anonymise.md` sans PII résiduelle, et le mode texte collé affiche le texte anonymisé
  réf: tests-perso/doc_test_rgpd.txt, src/ia_v7/services/commands.py
- [P2] Vérifier l'efficacité du renforcement de la consigne `DELIVERABLE_INSTRUCTION` (livrables non systématiquement mis en bloc ```livrable``` par le modèle Ollama).
  fait quand: observation sur plusieurs échanges réels (reformulation, traduction, résumé) que le modèle respecte le bloc livrable sans manquement ; sinon envisager fallback client (détection + bouton "convertir en livrable") ou post-traitement serveur
  réf: src/ia_v7/services/chat.py (DELIVERABLE_INSTRUCTION)
- [P2] Décider des extensions `/rgpd` : chemins avec espaces, pseudonymes, noms sans civilité, PII écrites en lettres ou fragmentées.
  fait quand: périmètre standard et éventuel mode strict actés pour chaque cas ambigu
  réf: benchmarks/rapport_rgpd.md, src/ia_v7/services/commands.py

## Questions ouvertes

## Échéances

## Blocages

## Contexte chaud
- `/write` et `/rgpd` : en conversation éphémère, rien n'est persisté ; le texte collé à `/rgpd` avec PII est persisté en historique SQLite dans une conversation normale.
- Le benchmark `/rgpd` est reproductible : 21/26 cas conformes, 24/29 PII absentes littéralement et 21 cas obligatoires verrouillés.
- Les limites `/rgpd` restantes sont les noms sans civilité, pseudonymes et PII écrites en lettres ou fragmentées ; aucun NER ni mode strict n'est implémenté.
- Capture d'écran : `html2canvas` re-rend le DOM (fidélité non pixel-perfect) ; alternative `getDisplayMedia` écartée (prompt à chaque capture, non testable).
- `/start` signale désormais les fichiers présents dans `rapports_erreurs_manuels/` (sans les lire).
- La consigne `DELIVERABLE_INSTRUCTION` est un prompt système, pas du code déterministe : son respect par le modèle local n'est pas garanti même renforcée. Le fallback côté client a été écarté pour l'instant (choix explicite).

## Dernière session (2026-07-17)
<!-- Écrasé intégralement par /close. Synthèse < 25 lignes. -->
# Session du 2026-07-17

## Décisions prises
- Le benchmark `/rgpd` utilise un corpus synthétique, une comparaison exacte et des seuils de non-régression.
- Les améliorations déterministes prioritaires sont appliquées ; les cas ambigus restent hors du périmètre standard.

## Livrables produits ou modifiés
- `benchmarks/rgpd_corpus.json`, `scripts/benchmark_rgpd.py`, `benchmarks/rapport_rgpd.md` : benchmark et rapport généré.
- `src/ia_v7/services/commands.py` : anonymisation renforcée pour IBAN, IPv4, cartes, adresses et emails Unicode.
- `tests/test_commands.py`, `tests/test_benchmark_rgpd.py` : couverture des règles et du benchmark.

## Hypothèses validées / invalidées
- VALIDE : le benchmark atteint 21/26 cas conformes, 24/29 PII absentes littéralement et ses seuils sont respectés.
- EN ATTENTE : test manuel applicatif `/rgpd`, efficacité de `DELIVERABLE_INSTRUCTION` et décision de périmètre des cas ambigus.

## Prochaine étape exacte
Lancer `python run.py`, tester `/rgpd tests-perso/doc_test_rgpd.txt`, puis vérifier le texte collé dans l'interface.

## Question bloquante pour la session suivante
Aucune
