# Les mesures — et comment les refaire

Ce document contient la **baseline** mesurée sur une session réelle, et la
méthode pour la re-mesurer sur votre poste. Les chiffres ne sont pas des
estimations : ils sortent des transcriptions locales que Claude Code écrit
lui-même.

## La baseline

Session de travail sur un dépôt PHP/Laravel, un jour, quatre chantiers menés
en parallèle par des sous-agents.

| | |
|---|---|
| Tours de modèle | 2 272 |
| Contexte moyen par tour | 200,9 k |
| Jetons écrits (sortie) | 3,9 M (0,8 %) |
| Jetons relus (cache + entrée) | 456,4 M (99,2 %) |
| Total traité | 460,3 M |

Le travail livré : **un commit de 71 fichiers**, 3 936 lignes ajoutées.

### La décomposition par acteur

| Acteur | Tours | Total | Écrit | Relu |
|---|---|---|---|---|
| Chaîne principale | 986 | 247,8 M | 0,45 M | 247,3 M |
| Agent « facture imprimable » | 433 | 69,8 M | 1,4 M | 68,3 M |
| Agent « lien portail » | 351 | 69,5 M | 0,32 M | 69,2 M |
| Agent « comptes du projet » | 347 | 58,8 M | 0,34 M | 58,4 M |
| Agent « modèle d'import » | 155 | 14,4 M | 0,06 M | 14,3 M |

**La leçon du tableau.** Deux agents, même type de tâche, même jour : l'un a
coûté 69,8 M, l'autre 14,4 M — un rapport de **4,8×**. Ce qui les sépare
n'est pas la difficulté : c'est le **nombre de tours** (433 contre 155) et
le **contexte moyen** que chacun a porté. Un agent qui lit 200 fois avant
d'écrire 30 fois paie 200 relectures de contexte.

### Les tours les plus chers

| Jour | Coût | Tours | Par tour |
|---|---|---|---|
| 2026-11-04 | 515,2 M | 1 712 | 300,9 k |

**Un seul prompt**, suivi de 1 712 tours, à 300 k renvoyés à chaque fois.
C'est la forme exacte du runaway : un chat qui dure, et une IA qui rend la
conversation de plus en plus lourde à chaque aller-retour.

### Ce qui a été gâché, en clair

| Geste | Coût estimé | Évitable |
|---|---|---|
| ~50 sondages pendant les attentes | ~12 M | oui — une commande en arrière-plan notifie, on ne sonde pas |
| 40 refus de la porte de première écriture | ~10 M | oui — préparer le grep et les faits avant le premier essai |
| 4 suites complètes au lieu d'une | ~8 M | oui — les portes une fois, à la fin |
| Le contexte qui grossit de 10 k à 500 k | le reste | oui — `/clear` entre deux tâches |

## La méthode

### Mesurer

```bash
ctx-cost                      # tous les jours
ctx-cost --day 2026-11-14     # un jour
ctx-cost --json               # pour un traitement automatisé
```

L'outil lit `~/.claude/projects/**/*.jsonl` et additionne quatre compteurs par
réponse de modèle : `input_tokens`, `cache_read_input_tokens`,
`cache_creation_input_tokens`, `output_tokens`.

### Ce qu'il faut regarder

1. **La part de relecture.** Au-dessus de 90 %, la facture est du transport,
   pas du travail. En dessous de 70 %, la répartition est saine.
2. **Le contexte moyen par tour.** Au-dessus de 120 k, la session est trop
   longue : elle aurait dû être coupée.
3. **Le tableau des agents.** Un agent qui coûte 5× un autre pour le même
   type de travail a un problème de **brief**, pas de modèle : on lui a trop
   laissé chercher.

### Comparer

Le seul juge de paix est la **base** : mesure avant, mesure après, même
tâche, même dépôt. `ctx-cost --day` donne le numéro ; le reste est de
l'intuition.

## Les limites de la mesure

- Le compteur mesure ce que le **modèle** a reçu, pas ce qui a été facturé :
  la lecture du cache est facturée moins cher que l'entrée neuve. Les
  proportions restent justes ; le montant, non.
- Les sous-agents sont comptés à part : leur contexte est le leur.
- Les sessions des autres machines ne sont pas visibles : le tableau de bord
  du fournisseur est la seule vue complète.
- `/usage` (la commande intégrée) donne les totaux de la session courante ;
  `ctx-cost` donne la **décomposition** — c'est ce que la commande intégrée
  ne dit pas.
