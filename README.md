# vcam-ai-ecosystem

**Un poste qui brûle 250 M de jetons pour un commit.** Ce dépôt contient la
réponse : un plugin, des hooks, des agents et deux outils qui changent la
facture — installables en deux minutes sur n'importe quel poste.

---

## Le problème, mesuré

Ce n'est pas une impression. Voici une session réelle, mesurée sur les
transcriptions locales (les dates sont effacées, la forme est celle qu'on
observe partout) :

| | |
|---|---|
| Tours de modèle (aller-retours) | **2 272** |
| Contexte moyen renvoyé à chaque tour | **200,9 k** |
| Jetons **écrits** (le travail réel) | **3,9 M** — 0,8 % |
| Jetons **relus** (la conversation réexpédiée) | **456,4 M** — 99,2 % |
| **Total** | **460,3 M** |

Le travail utile — un commit de 71 fichiers — est **la plus petite partie de
la facture**. Le reste est du transport.

**Pourquoi.** À chaque tour, Claude Code renvoie *toute* la conversation au
modèle. Le coût n'est donc pas « ce que l'IA fait », c'est :

```
coût  =  nombre de tours  ×  taille du contexte  ×  prix du jeton
```

Une session de six heures relit 200 k à chaque tour. Cent tours, c'est
vingt millions de jetons — pour une question d'une ligne.

Et le pire : le pire moment pour le découvrir est **après**. À 60 % de
contexte, la session a déjà payé deux fois ce qu'elle aurait coûté.

## La règle

> Le contexte coûte plus cher que le modèle.
> L'effort coûte plus cher que le modèle.
> **Mais le nombre de tours coûte plus cher que tout le reste.**

C'est pourquoi cet écosystème ne commence pas par « utilise un modèle moins
cher ». Il commence par **réduire les tours** et **réduire le contexte**.

---

## Ce qu'il y a dedans

### Le plugin `discipline`

| Élément | Ce qu'il fait |
|---|---|
| **Barre d'état** | Montre le **remplissage du contexte**, le coût, la branche, le taux de cache. Au-delà de 60 %, elle passe à l'orange et rappelle que `/clear` est gratuit. |
| **Hook `PreToolUse` (Bash)** | Les commandes de tests sont **tronquées à 120 lignes**. Le code de sortie est préservé : un test qui échoue échoue toujours. |
| **Hook `UserPromptSubmit`** | Mesure le contexte réel (dans la transcription) **avant** chaque tour. Au-delà de 55 %, il rappelle que `/clear` coûte zéro alors que `/compact` coûte une grosse requête. |
| **`/fin`** | Clore une session : les portes **une seule fois**, le commit, la mesure, et le `/clear` final. |
| **`/cout`** | Le rapport de consommation, **expliqué** — et une action concrète, pas un sermon. |
| **`/handoff`** | Écrit le prompt de relève de la session suivante, pour que rien ne soit redit. |
| **`/modele`** | Le routage par tâche, et le diagnostic « ton installation n'a qu'un seul modèle ». |
| **Agent `lecteur`** (`haiku`) | Lit le code et rend **40 lignes maximum**. |
| **Agent `testeur`** (`haiku`) | Lance la suite et rend **les seuls échecs**. |
| **Agent `reviseur`** (`sonnet`) | Relit un diff et rend les défauts classés, preuves à l'appui, **30 lignes maximum**. |
| **Skill `session-courte`** | La méthode et les chiffres, chargés à la demande. |

### Les outils (hors plugin, dans `~/.local/bin`)

| Outil | Rôle |
|---|---|
| **`ctx-cost`** | Le tableau de bord qui **explique** : par jour, par agent, la part de relecture, les prompts les plus chers, et une liste de leviers classés. |
| **`barre-etat`** | La ligne d'état. |

---

## Installation

```bash
git clone <url-de-ce-dépôt> ~/vcam-ai-ecosystem
cd ~/vcam-ai-ecosystem
./install.sh                       # pose les outils, propose les réglages
./install.sh --url <url-git>       # et enregistre la marketplace
```

Puis, dans Claude Code :

```
/plugin marketplace add ~/vcam-ai-ecosystem     # ou l'URL git
/plugin install discipline@vcam-ecosystem
```

Redémarre la session : les hooks et la barre d'état se chargent au
démarrage.

**L'installateur n'écrase rien.** Il n'ajoute que les clés **absentes** de
`~/.claude/settings.json` ; celles qui existent sont **rapportées**, et le
choix reste à l'humain. Une sauvegarde `settings.json.bak` est faite avant
toute écriture.

Pour désinstaller : `./install.sh --uninstall`.

---

## Les réglages posés, et pourquoi

| Clé | Valeur | Pourquoi |
|---|---|---|
| `statusLine` | `barre-etat` | Voir le contexte **avant** qu'il ne coûte. |
| `bashOutputMaxChars` | `20000` | Ce qui entre dans le contexte y reste, relu à chaque tour. 20 k suffisent à lire un échec. |
| `crossSessionInbound` | `"hold"` | Un message d'une autre session, delivered, est un tour complet qui renvoie tout le contexte. |
| `idleCompaction` | `false` | Compacter pendant une absence coûte une grosse requête pour rien. |
| `env.CLAUDE_CODE_AUTO_COMPACT_WINDOW` | `196608` (**recommandé**, pas appliqué) | On compacte à 200 k au lieu de 500 k : on relit moins longtemps. |

> Si `CLAUDE_CODE_AUTO_COMPACT_WINDOW` existe déjà chez vous, l'installateur
> **ne le touche pas** et vous le signale. Changez-le à la main si vous
> voulez le gain — c'est le levier le plus fort de la liste.

---

## La politique de modèle

| Tâche | Modèle | Effort |
|---|---|---|
| Lire, chercher, résumer, lancer des tests, compter | **le plus léger** | `low` |
| Écrire, corriger, déboguer, relire un diff | **le milieu** | `medium` |
| Architecture, conception, arbitrage de droits, migration | **le plus lourd** | `high` / `max` |

Et l'avertissement que `/modele` vérifie sur votre poste : **si les trois
alias de modèle pointent vers le même modèle**, le routage par modèle est
*inactif* — il n'y a qu'un prix. Dans ce cas, les leviers sont le contexte et
l'effort.

---

## Ce qu'on attend

| Avant | Après |
|---|---|
| Une session de 2 272 tours, 200 k de contexte moyen | Une session de 200 tours, 30 k de contexte moyen |
| 99,2 % de relecture | sous 80 %, et une action à chaque seuil |
| La facture se découvre à la fin, dans le tableau de bord | La barre d'état dit le contexte à chaque tour |

La mesure reste : `ctx-cost`. Mais elle sert à **décider la prochaine
session**, pas à se sentir coupable de la dernière.

---

## Pour aller plus loin

- `docs/MESURES.md` — la baseline mesurée, et la méthode pour la re-mesurer.
- `docs/POLITIQUE-MODELES.md` — le routage en détail, et ce qu'il faut faire
  quand un seul modèle est disponible.
- `docs/PLUGIN.md` — comment le plugin est fait, et les trois pièges de
  manifeste qui le font échouer **silencieusement**.
- Le dépôt est un **dépôt de plugins** : ajoute le tien dans
  `plugins/<ton-plugin>/` et il sera installable avec le même geste.

## Licence

MIT.
