---
description: Prend le contrôle de la souris et du clavier pour piloter uniquement l'UI IA_V7 ouverte à l'écran (screenshots, clics calculés, collage via presse-papiers)
argument-hint: [prompt à envoyer dans l'UI]
model: sonnet
---

# /controle_pc [prompt]

## Périmètre (impératif)

- Interagir **uniquement** avec la fenêtre de l'UI IA_V7 (SérénIA Tech), jamais avec une autre application, le bureau, l'explorateur de fichiers ou VSCode.
- Ne jamais cliquer ni taper en dehors de la zone de cette fenêtre.
- Aucune action destructive dans l'UI (suppression de dossier/conversation) sans confirmation explicite de l'utilisateur avant le clic.
- Ne jamais coller de donnée sensible (secrets, tokens) dans l'UI via cette procédure.
- Si un screenshot montre autre chose que l'UI attendue (fenêtre déplacée, focus perdu, popup inattendue) : s'arrêter et demander à l'utilisateur de repositionner la fenêtre plutôt que de deviner.

## Script

`D:\ServOMorph\IA_V7\.claude\scripts\pc_control.ps1`, appelé via l'outil PowerShell avec `dangerouslyDisableSandbox: true` (interaction avec le bureau réel, hors sandbox du repo).

Actions disponibles :
- `findwindow -Text <sous-chaîne du titre>` → JSON `{Title,Left,Top,Right,Bottom}` de la fenêtre dont le titre contient ce texte (ex. "SérénIA"). C'est la source de vérité pour délimiter la zone autorisée — ne jamais déduire cette zone en devinant une moitié d'écran sur un screenshot.
- `bounds` → JSON `{Left,Top,Width,Height}` de l'écran virtuel entier (rarement utile directement : sert seulement de repère global, pas de périmètre de clic).
- `screenshot -OutPath <chemin.png>` → capture l'écran complet, retourne le chemin du fichier.
- `click -X <int> -Y <int> [-MinX <int>] [-MaxX <int>] [-MinY <int>] [-MaxY <int>]` → clic gauche à la position donnée ; refuse le clic si une des bornes fournies est dépassée.
- `doubleclick -X <int> -Y <int> [-MinX/-MaxX/-MinY/-MaxY <int>]`
- `move -X <int> -Y <int>`
- `paste -Text "<texte>"` → place `<texte>` dans le presse-papiers puis simule Ctrl+V.
- `key -Key ENTER|ESCAPE|TAB`

Les captures et les clics viennent du même processus PowerShell : le repère de coordonnées est cohérent entre eux même si l'échelle DPI de l'écran diffère de 100 %. Ne pas mélanger avec des coordonnées lues ailleurs (autre outil, autre échelle).

## Procédure

1. **Bornage.** Appeler `findwindow -Text "SérénIA"` (ou un autre extrait stable du titre de la fenêtre de l'UI) pour obtenir son rectangle exact `{Left,Top,Right,Bottom}`. Réutiliser ces quatre valeurs comme `-MinX/-MaxX/-MinY/-MaxY` pour tous les clics de cette session — c'est le garde-fou technique qui empêche de cliquer ailleurs que dans cette fenêtre précise. Ne jamais approximer cette zone à partir d'une moitié d'écran supposée : la position et la taille réelles de la fenêtre ne correspondent pas forcément à un partage 50/50 de l'écran virtuel.

2. **Screenshot initial.** Appeler `screenshot` avec un `-OutPath` dans le dossier scratchpad de session, puis lire l'image produite avec l'outil Read. Identifier visuellement dans l'image l'élément cible (champ de saisie, bouton, dossier, etc.) et ses coordonnées pixel dans le repère de la capture (donc dans le repère `bounds`, pas dans un repère redimensionné).

3. **Vérification du périmètre.** Confirmer que les coordonnées calculées sont bien à l'intérieur du rectangle obtenu à l'étape 1. Si l'élément cible est hors de cette zone, s'arrêter : ce n'est pas une action autorisée par cette commande.

4. **Clic.** Appeler `click -X <x> -Y <y> -MinX <Left> -MaxX <Right> -MinY <Top> -MaxY <Bottom>` sur l'élément cible (ex. le champ de saisie du chat).

5. **Confirmation du focus.** Reprendre un `screenshot` et le relire avant de taper quoi que ce soit, pour vérifier que le focus est bien dans le bon champ (curseur clignotant, bordure active, bon dossier/conversation sélectionné).

6. **Saisie.** Appeler `paste -Text "<prompt>"` avec le texte à envoyer (le prompt fourni en argument de la commande, ou un texte demandé explicitement par l'utilisateur). Ne jamais utiliser `key` caractère par caractère pour du texte — `paste` géère correctement les accents et l'unicode.

7. **Relecture avant validation.** Reprendre un `screenshot`, le relire, et comparer visuellement le texte collé au texte attendu. Ne passer à l'étape suivante que si le contenu affiché correspond exactement.

8. **Validation.** Si l'action est un envoi de message (bouton "Envoyer" ou touche Entrée) : cliquer le bouton correspondant repéré sur le screenshot, ou `key -Key ENTER` seulement si le champ ciblé est une zone de saisie mono-ligne où Entrée envoie (vérifier via l'analyse de l'UI avant, cf. `static/js/app.js` — Entrée envoie, Maj+Entrée fait un saut de ligne).

9. **Screenshot final.** Reprendre un `screenshot` après validation pour confirmer visuellement le résultat (message envoyé, réponse en cours de streaming, etc.) et le rapporter à l'utilisateur.

## Notes

- Chaque capture doit être relue (outil Read) avant toute décision de coordonnées ou de validation — ne jamais cliquer "à l'aveugle" sur une position supposée sans l'avoir vérifiée sur un screenshot récent.
- En cas de doute sur une coordonnée (élément petit, ambigu), recadrer/zoomer mentalement en demandant un screenshot et en raisonnant sur une portion de l'image plutôt que de cliquer approximativement.
- Les fichiers de capture vont dans le dossier scratchpad de session, jamais dans le dépôt.
