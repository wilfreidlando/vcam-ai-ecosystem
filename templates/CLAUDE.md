# Règles d'engagement — consumption

Ces règles s'appliquent à **toutes les sessions** de ce poste. Elles ne
changent pas ce qui est livré : elles changent la **facture**.

Le coût d'une session n'est pas le travail, c'est la **relecture** : à chaque
tour, toute la conversation est renvoyée au modèle. Donc :

```
coût = nombre de tours × taille du contexte × prix du jeton
```

## Une session = un chantier

Quand une tâche est terminée et que la suivante n'a rien à voir avec elle :
**`/clear`**. C'est **gratuit**. `/compact` coûte une grosse requête — c'est
le mauvais réflexe.

Ne jamais enchaîner deux chantiers sans `/clear` entre les deux.

## Déléguer ce qui n'a pas besoin de la session principale

Quand la tâche est **lire, chercher, localiser, résumer, compiler ou lancer
des tests** :

| Besoin | Agent | Modèle |
|---|---|---|
| Lire, chercher, localiser, résumer | `discipline:lecteur` | le plus léger, effort `low` |
| Lancer une suite, rapporter les échecs | `discipline:testeur` | le plus léger, effort `low` |
| Relire un diff, classer les défauts | `discipline:reviseur` | le milieu |

**Trois règles impératives :**

1. L'agent rend un **résumé**, jamais la sortie brute. Une sortie de test de
   40 000 lignes ne revient pas dans la conversation principale.
2. **Une seule** question par agent. Un agent qui doit chercher dix choses
   coûte dix fois son prix.
3. Ne pas déléguer ce qui exige le contexte de la session (une décision
   d'architecture, un arbitrage qui dépend de ce qui a été dit avant).

## Ce qui ne se délègue pas

Écrire, corriger, déboguer, et tout ce qui dépend de ce qui précède : ça
reste dans la session principale, au modèle du milieu.

## Outils

- `ctx-cost` — le rapport de consommation, expliqué. À lancer à la fin d'une
  session, ou au début pour savoir dans quoi on s'engage.
- `/cout`, `/fin`, `/handoff`, `/modele` — les quatre commandes de la
  discipline. `/fin` ferme proprement une session ; `/handoff` écrit le
  prompt de relève pour la suivante.
- La barre d'état sous l'invite montre le **remplissage du contexte** : la
  regarder coûte une seconde et évite une facture.

## Ce que je ne fais pas

- Je ne sonde pas les commandes en arrière-plan : une commande en
  arrière-plan notifie, on ne boucle pas.
- Je ne lance pas deux suites de tests à la fois sur la même base.
- Je ne ramène pas dans le contexte principal la sortie brute d'un agent.

---

*Ces règles viennent du dépôt `vcam-ai-ecosystem` (plugin `discipline`).
Pour les adopter sur un autre poste : copiez ce fichier dans
`~/.claude/CLAUDE.md` (portée utilisateur) ou à la racine de vos dépôts
(portée projet).*
