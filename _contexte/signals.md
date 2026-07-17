# Signals — ia_v7   (MAJ 2026-07-17)

## Actions ouvertes
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
- Rapport dans `rapports_erreurs_manuels/` (capture) mal interprété au départ : implémentation d'une modal `/rgpd` faite puis annulée (`git checkout`) après clarification.
- Vrai problème identifié : le modèle Ollama a répondu en texte brut au lieu d'utiliser le bloc ```livrable``` lors d'une reformulation.
- Choix : renforcer la consigne système `DELIVERABLE_INSTRUCTION` (formulation plus impérative) plutôt que fallback client ou aucune action.

## Livrables produits ou modifiés
- src/ia_v7/services/chat.py : `DELIVERABLE_INSTRUCTION` reformulée (consigne plus stricte, déclencheurs élargis)

## Hypothèses validées / invalidées
- EN ATTENTE : efficacité du renforcement de la consigne — non vérifiable de façon déterministe, dépend du comportement du modèle en usage réel.

## Prochaine étape exacte
Observer en usage réel si le modèle respecte mieux la consigne livrable ; si récidive, statuer sur un fallback client ou un post-traitement serveur. Puis reprendre le test manuel de `/rgpd`.

## Question bloquante pour la session suivante
Aucune.
