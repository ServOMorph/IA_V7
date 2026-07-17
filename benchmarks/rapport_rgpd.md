# Rapport du benchmark `/rgpd`

Corpus : `rgpd_corpus.json` — version 1 — données synthétiques uniquement.

## Résumé

| Indicateur | Résultat | Seuil |
|---|---:|---:|
| Cas exactement conformes | 21/26 (80,8 %) | 75,0 % |
| PII attendues absentes littéralement | 24/29 (82,8 %) | 80,0 % |
| Cas obligatoires conformes | 21/21 | 100,0 % |
| Seuils de non-régression | respectés | — |

> Le rappel littéral indique qu'une valeur complète n'est plus présente. Il ne garantit pas qu'une PII partiellement anonymisée soit sûre ; la conformité exacte reste l'indicateur principal.

## Résultats par difficulté

| Difficulté | Conformes | Total | Taux |
|---|---:|---:|---:|
| facile | 6 | 6 | 100,0 % |
| moyen | 4 | 4 | 100,0 % |
| difficile | 5 | 5 | 100,0 % |
| très difficile | 4 | 6 | 66,7 % |
| adversarial | 2 | 5 | 40,0 % |

## Résultats par catégorie

| Catégorie | PII attendues | Absentes littéralement | Rappel littéral |
|---|---:|---:|---:|
| adresse | 2 | 2 | 100,0 % |
| carte | 1 | 1 | 100,0 % |
| email | 8 | 6 | 75,0 % |
| iban | 4 | 4 | 100,0 % |
| ip | 1 | 1 | 100,0 % |
| nir | 1 | 1 | 100,0 % |
| nom | 5 | 4 | 80,0 % |
| pseudo | 1 | 0 | 0,0 % |
| telephone | 6 | 5 | 83,3 % |

## Détail des écarts

### `tres_difficile_nom_sans_civilite` — Nom sans civilité

- Difficulté : très difficile
- Type d'écart : faux négatif
- Remplacements attendus/obtenus : 1/0
- Attendu : `Le contact principal est [DONNÉE_SENSIBLE]`
- Obtenu : `Le contact principal est Jean Dupont`
- Piste : Ajouter une détection de noms contextualisée ; une regex générale créerait trop de faux positifs.

### `tres_difficile_pseudo` — Pseudonyme de compte

- Difficulté : très difficile
- Type d'écart : faux négatif
- Remplacements attendus/obtenus : 1/0
- Attendu : `Compte public : [DONNÉE_SENSIBLE]`
- Obtenu : `Compte public : @client_confidentiel`
- Piste : Décider explicitement si les pseudonymes font partie du périmètre PII.

### `adversarial_email_mots` — Email écrit en toutes lettres

- Difficulté : adversarial
- Type d'écart : faux négatif
- Remplacements attendus/obtenus : 1/0
- Attendu : `Contact : [DONNÉE_SENSIBLE]`
- Obtenu : `Contact : jean point dupont arobase exemple point fr`
- Piste : Prévoir une normalisation optionnelle des formes « point » et « arobase », avec contrôle des faux positifs.

### `adversarial_email_fragmente` — Email fragmenté sur plusieurs lignes

- Difficulté : adversarial
- Type d'écart : faux négatif
- Remplacements attendus/obtenus : 1/0
- Attendu : `Contact : [DONNÉE_SENSIBLE]`
- Obtenu : `Contact : alice\n@example\n.fr`
- Piste : Définir si la recomposition interligne est acceptable avant d'ajouter ce cas à la détection.

### `adversarial_telephone_mots` — Téléphone partiellement écrit en lettres

- Difficulté : adversarial
- Type d'écart : faux négatif
- Remplacements attendus/obtenus : 1/0
- Attendu : `Appelez [DONNÉE_SENSIBLE]`
- Obtenu : `Appelez zéro six 12 34 56 78`
- Piste : Une détection des nombres en lettres nécessite une normalisation linguistique dédiée.

## Pistes d'amélioration prioritaires

- Ajouter une détection de noms contextualisée ; une regex générale créerait trop de faux positifs.
- Décider explicitement si les pseudonymes font partie du périmètre PII.
- Prévoir une normalisation optionnelle des formes « point » et « arobase », avec contrôle des faux positifs.
- Définir si la recomposition interligne est acceptable avant d'ajouter ce cas à la détection.
- Une détection des nombres en lettres nécessite une normalisation linguistique dédiée.

## Reproduction

```powershell
python scripts/benchmark_rgpd.py
```
