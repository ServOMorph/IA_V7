# Signals — ia_v7   (MAJ 2026-07-17)

## Actions ouvertes
- [P1] Test manuel de `/rgpd` dans l'app lancée (`python run.py`), sur le fichier de démo.
  fait quand: `/rgpd tests-perso/doc_test_rgpd.txt` produit `doc_test_rgpd_anonymise.md` sans PII résiduelle, et le mode texte collé affiche le texte anonymisé
  réf: tests-perso/doc_test_rgpd.txt, src/ia_v7/services/commands.py
- [P2] Décider des extensions `/rgpd` : chemins avec espaces (traités comme texte aujourd'hui), motifs supplémentaires, détection des noms sans civilité (NER).
  fait quand: décision actée (go/no-go par extension) dans une session
  réf: src/ia_v7/services/commands.py (SENSITIVE_PATTERNS, _looks_like_path)

## Questions ouvertes

## Échéances

## Blocages

## Contexte chaud
- `/write` et `/rgpd` : en conversation éphémère, rien n'est persisté ; le texte collé à `/rgpd` avec PII est persisté en historique SQLite dans une conversation normale.
- Limites `/rgpd` documentées dans `/help` : noms sans civilité non détectés (regex, pas de NER).
- Capture d'écran : `html2canvas` re-rend le DOM (fidélité non pixel-perfect) ; alternative `getDisplayMedia` écartée (prompt à chaque capture, non testable).
- `/start` signale désormais les fichiers présents dans `rapports_erreurs_manuels/` (sans les lire).

## Dernière session (2026-07-17)
<!-- Écrasé intégralement par /close. Synthèse < 25 lignes. -->
# Session du 2026-07-17

## Décisions prises
- `/rgpd` : anonymisation par regex (pas de LLM, non-déterminisme jugé risqué) ; en mode fichier, écriture directe de `<original>_anonymise.md` (pas de confirmation interactive, flux one-shot).
- Capture d'écran via `html2canvas` vendorisé, endpoint `POST /api/ia/captures`, PNG horodatés dans `rapports_erreurs_manuels/` (`IA_V7_CAPTURES_DIR`).
- `MAX_CONTENT_LENGTH` porté de 1 Mo à 10 Mo (PNG base64).
- `/start` liste les fichiers de `rapports_erreurs_manuels/` sans les lire (bloc spécificités projet de start.md).

## Livrables produits ou modifiés
- src/ia_v7/services/commands.py : commande `/rgpd` (texte + fichier), `raw_text` dans CommandContext
- src/ia_v7/web/routes.py, config.py, app.py : endpoint captures, réglage `captures_dir`, limite 10 Mo
- static/js/app.js, styles.css, templates/index.html : bouton Capture, overlay rectangle (tracé/déplacement/poignées), toast
- static/vendor/html2canvas.min.js : ajouté
- tests/, tests-ui/ui.spec.js, conftest.py, scripts serveurs UI : couverture complète (46 pytest, Playwright vert)
- tests-perso/doc_test_rgpd.txt : fichier de démo PII fictives ; rapports_erreurs_manuels/ créé
- .claude/commands/start.md : signalement des rapports d'erreur en attente

## Hypothèses validées / invalidées
- VALIDE : le flux capture écrit un vrai PNG (vérifié : 360x260 produit par le test UI).
- EN ATTENTE : comportement réel de `/rgpd` en conditions manuelles (app lancée).

## Prochaine étape exacte
Test manuel de `/rgpd` sur tests-perso/doc_test_rgpd.txt (mode fichier puis mode texte collé), puis statuer sur les extensions (chemins avec espaces, motifs, NER).

## Question bloquante pour la session suivante
Aucune.
