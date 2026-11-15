---
description: Quel modèle pour quelle tâche — le routage, et ce que l'effort coûte
---

# /modele — le routage

Tu demandes comment router le travail entre les modèles. Réponds en **tableau
et en décisions**, jamais en récitation de la documentation.

## La règle simple

| Tâche | Modèle | Pourquoi |
|---|---|---|
| Lire, chercher, résumer, compiler des tests, compter, lister | **le plus léger** (haiku) | Le résultat tient en dix lignes ; le modèle lourd n'apporte rien |
| Écrire du code, corriger, déboguer, revue de diff | **le milieu** (sonnet) | Le rapport qualité/prix est là |
| Architecture, choix de conception, plan de lots, arbitrage de droits, migration | **le plus lourd** (opus) | C'est là que le raisonnement long paie |

Et l'**effort** suit la même logique : `low` pour le mécanique, `medium` pour
le travail normal, `high`/`max` pour la conception et le diagnostic difficile.
Les jetons de raisonnement sont **facturés comme des jetons de sortie** : un
effort `max` sur une tâche mécanique est du gaspillage pur.

## Les trois leviers, dans l'ordre du rendement

1. **Le contexte** : il coûte plus cher que le modèle. Un `/clear` entre
   deux tâches vaut mieux qu'un modèle moins cher sur une session longue.
2. **Le modèle** : il change le prix du jeton, pas le nombre de jetons.
3. **L'effort** : il change le nombre de jetons de sortie, donc directement
   la facture.

## Ce que tu fais, concrètement

1. Lis la configuration en vigueur : `~/.claude/settings.json` (les clés
   `model`, `modelSettings`, `env.ANTHROPIC_DEFAULT_*_MODEL`).
2. Si les trois alias (`ANTHROPIC_DEFAULT_OPUS_MODEL`, `…_SONNET_MODEL`,
   `…_HAIKU_MODEL`) pointent **vers le même modèle**, dis-le franchement :
   le routage par modèle est alors **inactif** — il n'y a qu'un prix. Dans
   ce cas, le levier est l'effort et le contexte, pas le modèle.
3. Propose un réglage concret : les valeurs de `modelSettings` à écrire,
   et le `model:` à mettre dans les sous-agents (un sous-agent qui lit peut
   être en `haiku` sans que personne ne le voie).
4. Si tu peux agir (les fichiers sont accessibles), **agis** : c'est le rôle
   de cette commande.

Ne moralise pas sur la dépense. Le but est une décision par tâche.
