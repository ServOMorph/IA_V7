# Signals — ia_v7   (MAJ 2026-07-17)

## Actions ouvertes
- [P1] Construire un benchmark automatisé de `/rgpd` (demande utilisateur, session 2026-07-17, non commencé — à démarrer en priorité).
  Idée : fournir des textes de difficulté croissante à `anonymize_text()`, comparer aux PII attendues, produire un rapport lisible (résultats + pistes d'amélioration).
  Difficultés déjà explorées avant l'interruption (à valider avec l'utilisateur en début de session) :
    1. Facile : email/téléphone/IBAN isolés, format standard
    2. Moyen : adresses postales, noms avec civilité, NIR
    3. Difficile : formats atypiques (tél. sans espaces, IBAN espacé différemment, email en continu)
    4. Très difficile : noms SANS civilité (limite connue, non détectée par regex), pseudos, PII en tableau/CSV, plusieurs PII par phrase, faux positifs potentiels
    5. Adversarial : PII obfusquées volontairement (ex. "jean point dupont at gmail point com"), homoglyphes unicode, PII fragmentées sur plusieurs lignes
  Code de référence lu : src/ia_v7/services/commands.py — `SENSITIVE_PATTERNS` (l.129-144), `anonymize_text()` (l.147-152), `_handle_rgpd()` (l.164-206).
  Fichier de test existant : tests-perso/doc_test_rgpd.txt (cas simple, déjà utilisé pour test manuel /rgpd).
  Décisions NON prises (à trancher en début de session suivante) :
    - Emplacement du script/corpus (probablement tests-perso/ ou un nouveau dossier dédié benchmark)
    - Format du ground truth (comptage par catégorie vs correspondance exacte de spans)
    - Sortie : script Python (pytest ou standalone) + rapport Markdown généré automatiquement
  réf: src/ia_v7/services/commands.py, tests-perso/doc_test_rgpd.txt
- [P1] Test manuel de `/rgpd` dans l'app lancée (`python run.py`), sur le fichier de démo.
  fait quand: `/rgpd tests-perso/doc_test_rgpd.txt` produit `doc_test_rgpd_anonymise.md` sans PII résiduelle, et le mode texte collé affiche le texte anonymisé
  réf: tests-perso/doc_test_rgpd.txt, src/ia_v7/services/commands.py
- [P2] Vérifier l'efficacité du renforcement de la consigne `DELIVERABLE_INSTRUCTION` (livrables non systématiquement mis en bloc ```livrable``` par le modèle Ollama).
  fait quand: observation sur plusieurs échanges réels (reformulation, traduction, résumé) que le modèle respecte le bloc livrable sans manquement ; sinon envisager fallback client (détection + bouton "convertir en livrable") ou post-traitement serveur
  réf: src/ia_v7/services/chat.py (DELIVERABLE_INSTRUCTION)
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
- La consigne `DELIVERABLE_INSTRUCTION` est un prompt système, pas du code déterministe : son respect par le modèle local n'est pas garanti même renforcée. Le fallback côté client a été écarté pour l'instant (choix explicite).

## Dernière session (2026-07-17)
<!-- Écrasé intégralement par /close. Synthèse < 25 lignes. -->
# Session du 2026-07-17

## Décisions prises
- Rapport de capture dans `rapports_erreurs_manuels/` traité manuellement par l'utilisateur : fichier supprimé (demande explicite).
- Nouvelle idée actée : construire un benchmark automatisé de `/rgpd` (textes de difficulté croissante, rapport lisible + pistes d'amélioration). Session interrompue avant tout code.

## Livrables produits ou modifiés
- rapports_erreurs_manuels/capture_20260717_200640.png : supprimé (traité).
- _contexte/signals.md : ajout de l'action benchmark `/rgpd` avec contexte détaillé.

## Hypothèses validées / invalidées
- EN ATTENTE : efficacité du renforcement de `DELIVERABLE_INSTRUCTION` (reportée, pas observée cette session).

## Prochaine étape exacte
Démarrer le benchmark `/rgpd` : trancher emplacement du script/corpus, format du ground truth, puis construire corpus de difficulté croissante + script de scoring + rapport Markdown. Voir action [P1] détaillée ci-dessus.

## Question bloquante pour la session suivante
Aucune (décisions de conception à trancher en session, pas bloquantes pour démarrer).
