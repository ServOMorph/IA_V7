# IA V7

Application autonome extraite du module IA de l’interface SérénIA Tech. Elle pilote Ollama local, gère les dossiers et conversations, conserve l’historique dans une base SQLite dédiée et diffuse les réponses en streaming.

## État actuel

Système de commandes `/xxx` intercepté côté serveur, livré et testé (backend + UI). Commandes disponibles : `/help`, `/write <nom_fichier> [<path>]`, `/rgpd <chemin_fichier | texte>` (anonymisation des données sensibles par regex ; depuis un fichier, écrit `<original>_anonymise.md` à côté ; les noms sans civilité ne sont pas détectés).

Capture d'écran intégrée à l'interface : bouton « Capture », sélection d'un rectangle ajustable, PNG horodaté enregistré dans `rapports_erreurs_manuels/` (`IA_V7_CAPTURES_DIR`).

La consigne système imposant au modèle de placer tout texte réutilisable dans un bloc ```livrable``` a été reformulée de façon plus impérative (respect non garanti, dépend du modèle Ollama utilisé).

## Prérequis

- Windows 10 ou 11 ;
- Python 3.11 ou supérieur ;
- Node.js 20 ou supérieur pour les tests d’interface ;
- Microsoft Edge à jour pour les tests Playwright ;
- Ollama installé et disponible dans `PATH` ;
- au moins un modèle Ollama installé.

## Installation

```powershell
cd D:\ServOMorph\IA_V7
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Lancement

```powershell
python run.py
```

L’interface est disponible sur `http://127.0.0.1:4023`.

Options :

```powershell
python run.py --host 127.0.0.1 --port 4023
python run.py --help
```

La configuration peut être adaptée avec un fichier `.env` basé sur `.env.example`.

## Tests automatisés

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
npm ci
npm run test:ui
npm run test:ui:real
```

`test:ui` utilise un faux Ollama déterministe et une base temporaire. `test:ui:real` réalise un échange complet depuis Edge avec l’instance Ollama locale et `gemma4:e4b`, sans modifier la base migrée.

Le protocole fonctionnel complet se trouve dans [TESTS_MANUELS.md](TESTS_MANUELS.md).

## Données

- `data/ia.db` : dossiers, conversations, messages et faits mémorisés ;
- `data/default_model.txt` : modèle par défaut ;
- ces fichiers locaux sont exclus de Git.

La base actuelle a été extraite de `UI/sereniatech.db`. La migration n’embarque aucune table étrangère au module IA.

Pour refaire une extraction :

```powershell
python scripts\migrate_from_sereniatech.py "C:\chemin\vers\sereniatech.db" --target data\ia.db --replace
```

Si la base source contient des relations orphelines, la commande s’arrête. Après vérification, l’option explicite `--skip-orphans` permet d’exclure uniquement ces lignes.

## Architecture

```text
run.py                         lanceur direct
src/ia_v7/app.py               composition de l’application
src/ia_v7/config.py            configuration et chemins
src/ia_v7/web/routes.py        contrats HTTP
src/ia_v7/services/            logique de chat et de contexte
src/ia_v7/infrastructure/      SQLite, dépôts et client Ollama
templates/                     structure de l’interface
static/                        charte et comportement front-end
scripts/                       migration contrôlée
tests/                         tests API, domaine, migration et UI
```

Les dépendances externes sont injectables. Les routes ne dépendent ni du monolithe SérénIA Tech ni d’un chemin absolu historique.

## Point de vigilance

Le bouton `Arrêter serveur` conserve le comportement historique : sous Windows, il arrête le processus `ollama.exe`. Cela affecte les autres applications locales qui utilisent la même instance Ollama.
