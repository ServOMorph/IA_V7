# Tests manuels complets — IA V7

Date : 2026-07-17

## Conditions

- travailler dans `D:\ServOMorph\IA_V7` ;
- utiliser Edge, Chrome ou Firefox à jour ;
- disposer d’Ollama et d’au moins un modèle installé ;
- utiliser uniquement un dossier de test nommé `TEST_MANUEL_IA_V7` ;
- ne pas supprimer les conversations migrées.

Pour chaque échec, relever le numéro du test, l’heure, le navigateur, la largeur de fenêtre, le modèle sélectionné, le comportement observé et une capture d’écran.

## Procédure

### Test 01 — Installation propre

1. Créer et activer un environnement virtuel.
2. Exécuter `python -m pip install -r requirements.txt`.
3. Exécuter `python run.py --help`.

Résultat attendu : l’installation termine sans erreur et l’aide liste `--host`, `--port` et `--debug`.

### Test 02 — Lancement par `run.py`

1. Exécuter `python run.py`.
2. Vérifier le message `IA V7 disponible sur http://127.0.0.1:4023`.
3. Ouvrir cette adresse.

Résultat attendu : la page répond, sans erreur Python dans le terminal.

### Test 03 — Santé HTTP

1. Ouvrir `http://127.0.0.1:4023/api/ia/sante`.

Résultat attendu : la réponse est `{"ok":true}` avec un statut HTTP 200.

### Test 04 — Charte graphique

1. Vérifier l’en-tête `SérénIA Tech`, le fond, les bordures et les boutons.
2. Comparer visuellement les couleurs principales avec le module source.
3. Vérifier les polices Inter et Space Grotesk lorsque la connexion Internet est disponible.

Résultat attendu : dominante bleu-vert `rgb(165, 201, 202)`, surfaces et espacements cohérents avec l’interface SérénIA Tech, sans feuille de style manquante.

### Test 05 — Thème système clair et sombre

1. Passer Windows en thème clair, puis recharger la page.
2. Passer Windows en thème sombre, puis recharger la page.
3. Vérifier les textes, champs, boutons et bulles dans les deux modes.

Résultat attendu : le thème suit le réglage système et tous les contrôles restent lisibles.

### Test 06 — Affichage responsive

1. Tester aux largeurs 1440 px, 1024 px, 768 px et 390 px.
2. À 390 px, faire défiler le panneau des conversations puis le chat.
3. Vérifier la zone de saisie et tous les boutons de la barre de modèle.

Résultat attendu : aucun débordement horizontal bloquant ; sous 900 px, la liste des conversations se place au-dessus du chat.

### Test 07 — Chargement des données migrées

1. Vérifier la présence du dossier `Prompts Claude Code`.
2. Ouvrir ce dossier.
3. Ouvrir plusieurs conversations existantes.

Résultat attendu : les titres et historiques disponibles s’affichent sans erreur, sans contenu d’un autre module SérénIA Tech.

### Test 08 — État Ollama actif

1. Démarrer Ollama hors de l’application si nécessaire.
2. Recharger IA V7.
3. Observer la pastille, la liste des modèles et le badge du modèle chargé.

Résultat attendu : pastille verte, modèles locaux listés, bouton `Arrêter serveur` et badge exact du modèle en mémoire.

### Test 09 — État Ollama indisponible

1. Fermer IA V7 puis arrêter Ollama manuellement.
2. Relancer IA V7 et recharger la page.

Résultat attendu : pastille rouge, liste indiquant qu’Ollama est injoignable, interface toujours utilisable pour consulter l’historique.

### Test 10 — Démarrage d’Ollama depuis l’interface

1. Avec Ollama arrêté, cliquer `Démarrer serveur`.
2. Attendre au maximum 20 secondes.

Résultat attendu : la pastille devient verte, le bouton devient `Arrêter serveur` et les modèles apparaissent.

### Test 11 — Arrêt d’Ollama depuis l’interface

Attention : ce test ferme `ollama.exe` pour toutes les applications locales.

1. S’assurer qu’aucune autre application n’utilise Ollama.
2. Cliquer `Arrêter serveur`.
3. Attendre au maximum 20 secondes.

Résultat attendu : la pastille devient rouge et aucun processus Ollama ne reste actif.

### Test 12 — Chargement et déchargement d’un modèle

1. Démarrer Ollama.
2. Sélectionner un petit modèle disponible.
3. Cliquer `Charger modèle` et attendre la fin.
4. Vérifier le badge, puis cliquer `Décharger`.

Résultat attendu : le modèle apparaît puis disparaît du badge de mémoire, sans blocage permanent du bouton.

### Test 13 — Modèle par défaut

1. Sélectionner un modèle différent.
2. Cliquer `Défaut`.
3. Créer une nouvelle conversation.
4. Redémarrer IA V7 et créer une seconde conversation.

Résultat attendu : `Défaut ✓` apparaît ; les deux nouvelles conversations utilisent le modèle choisi, y compris après redémarrage.

### Test 14 — Création d’un dossier

1. Cliquer `+ Dossier`.
2. Saisir `TEST_MANUEL_IA_V7`.
3. Déplier le dossier.

Résultat attendu : le dossier apparaît dans l’ordre alphabétique et affiche `vide`.

### Test 15 — Renommage d’un dossier

1. Double-cliquer `TEST_MANUEL_IA_V7`.
2. Renommer en `TEST_MANUEL_IA_V7_RENOMME`, valider avec Entrée.
3. Recharger la page, puis rétablir `TEST_MANUEL_IA_V7`.

Résultat attendu : le nom est conservé après rechargement et le renommage par Échap n’enregistre aucune modification.

### Test 16 — Prompt système du dossier

1. Cliquer sur l’icône de réglage du dossier de test.
2. Saisir `Réponds toujours en français et en une phrase.`
3. Cliquer `Enregistrer`.
4. Créer une conversation dans ce dossier et envoyer une question simple.

Résultat attendu : confirmation `Enregistré ✓` et réponse respectant la consigne autant que le modèle le permet.

### Test 17 — Conversation persistante

1. Dans le dossier de test, cliquer `+`.
2. Vérifier le titre `Nouvelle conversation`.
3. Envoyer `Réponds uniquement : TEST OK.`.
4. Attendre la fin du streaming.

Résultat attendu : bulle utilisateur immédiate, indicateur animé, réponse reçue progressivement et boutons réactivés à la fin.

### Test 18 — Titre automatique

1. Après le premier échange du test 17, observer le titre.
2. Recharger la page.

Résultat attendu : un titre court remplace `Nouvelle conversation` et persiste après rechargement.

### Test 19 — Historique et ordre des messages

1. Envoyer deux autres messages dans la même conversation.
2. Ouvrir une autre conversation puis revenir.
3. Redémarrer le serveur et rouvrir la conversation de test.

Résultat attendu : tous les messages sont présents dans leur ordre initial après navigation et redémarrage.

### Test 20 — Renommage d’une conversation

1. Double-cliquer le titre dans l’arborescence.
2. Saisir `Conversation test manuelle` et valider.
3. Recharger la page.

Résultat attendu : le nouveau titre apparaît dans l’arborescence et la barre du chat, puis persiste.

### Test 21 — Changement de modèle en cours de conversation

1. Ouvrir la conversation de test.
2. Sélectionner un autre modèle.
3. Envoyer un message.

Résultat attendu : un marqueur `Modèle : …` apparaît et la réponse suivante utilise le nouveau modèle.

### Test 22 — Arrêt d’une génération

1. Demander une réponse longue.
2. Dès le début du streaming, cliquer `Stop`.

Résultat attendu : le flux visible s’arrête, la saisie et le bouton `Envoyer` redeviennent disponibles, sans rechargement de page.

### Test 23 — Markdown et code

1. Demander une réponse contenant un titre Markdown, une liste et un bloc de code.
2. Vérifier le rendu et le défilement horizontal du bloc de code.

Résultat attendu : structure Markdown lisible, code distinct, aucune balise HTML ou script non sûr exécuté.

### Test 24 — Livrable, copie et téléchargement

1. Demander `Produis un court texte réutilisable dans un bloc livrable`.
2. Cliquer `Copier` puis coller dans un éditeur texte.
3. Cliquer `Télécharger` et autoriser le téléchargement si le navigateur le demande.

Résultat attendu : seul le contenu du livrable est copié ; le fichier téléchargé utilise l’extension cohérente (`txt`, `md`, `json` ou `html`).

### Test 25 — Copie d’une réponse

1. Survoler une bulle assistant.
2. Cliquer `Copier` et coller dans un éditeur.

Résultat attendu : le texte brut complet est copié et le bouton affiche temporairement `Copié ✓`.

### Test 26 — Mode éphémère

1. Cocher `Mode éphémère`.
2. Créer une conversation et envoyer un message sans donnée sensible.
3. Recharger la page.

Résultat attendu : la réponse fonctionne mais la conversation et ses messages ne réapparaissent pas dans l’arborescence.

### Test 27 — Entrée et Maj+Entrée

1. Saisir deux lignes avec Maj+Entrée.
2. Appuyer sur Entrée seule.

Résultat attendu : Maj+Entrée crée un saut de ligne ; Entrée envoie le texte complet ; la zone grandit jusqu’à sa hauteur maximale.

### Test 28 — Erreur réseau pendant le chat

1. Envoyer une demande longue.
2. Arrêter Ollama pendant la génération.

Résultat attendu : une erreur lisible apparaît dans la bulle, la page ne plante pas et un nouvel essai reste possible après redémarrage d’Ollama.

### Test 29 — Suppression d’une conversation de test

1. Cliquer la croix de `Conversation test manuelle`.
2. Annuler la confirmation et vérifier qu’elle reste présente.
3. Recommencer puis confirmer.

Résultat attendu : l’annulation ne change rien ; la confirmation retire uniquement la conversation ciblée et ses messages.

### Test 30 — Suppression en cascade du dossier de test

1. Créer une nouvelle conversation dans `TEST_MANUEL_IA_V7`.
2. Cliquer la croix du dossier.
3. Annuler une première fois, puis confirmer au second essai.

Résultat attendu : l’annulation conserve le dossier ; la confirmation supprime le dossier et uniquement ses conversations.

### Test 31 — Redémarrage et intégrité finale

1. Arrêter IA V7 avec `Ctrl+C`.
2. Relancer `python run.py`.
3. Exécuter :

```powershell
sqlite3 -readonly data\ia.db "PRAGMA integrity_check; PRAGMA foreign_key_check;"
```

Résultat attendu : lancement normal, données historiques intactes, sortie SQLite `ok` sans ligne supplémentaire.

## Critères de validation

Le livrable est validé si les tests 01 à 31 passent, qu’aucune donnée migrée non créée pour le test n’est supprimée, que le terminal Flask ne contient aucune exception non traitée et que la base reste intègre.

