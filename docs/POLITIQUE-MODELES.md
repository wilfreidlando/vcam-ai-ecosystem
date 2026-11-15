# La politique de modèle

Comment décider **quel modèle** et **quel effort**, tâche par tâche, sans y
penser à chaque fois.

## Le principe

Il y a trois leviers, et ils ne se valent pas :

| Levier | Ce qu'il change | Ordre de grandeur |
|---|---|---|
| **Le contexte** | le nombre de jetons transportés | le plus fort |
| **L'effort** | le nombre de jetons de sortie | moyen |
| **Le modèle** | le prix unitaire du jeton | le plus faible |

Un modèle deux fois moins cher ne divise la facture que par deux — si le
contexte est le même. Or le contexte est précisément ce qui explose. **Le
routage par modèle est donc le dernier levier, pas le premier.**

## La table

| Tâche | Modèle | Effort | Pourquoi |
|---|---|---|---|
| Lire, chercher, résumer, lister, compter | **léger** (`haiku`) | `low` | La réponse tient en dix lignes ; le raisonnement long n'y ajoute rien |
| Lancer une suite de tests, en rendre le résultat | **léger** (`haiku`) | `low` | Un constat n'est pas une décision |
| Écrire du code, corriger, déboguer | **moyen** (`sonnet`) | `medium` | Le rapport qualité/prix est là |
| Relire un diff | **moyen** (`sonnet`) | `medium` | Il faut du jugement, pas de la vitesse |
| Concevoir, arbitrer, migrer, trancher un droit | **lourd** (`opus`) | `high` | C'est là que le raisonnement long paie |
| Diagnostiquer un échec obscur | **lourd** (`opus`) | `max` | Peu de tours, mais chacune doit compter |

## L'effort

Les jetons de raisonnement sont **facturés comme des jetons de sortie**. Un
effort `max` sur une tâche mécanique est du gaspillage pur, et invisible :
la facture monte, la qualité ne bouge pas.

- `/effort low` pour le mécanique.
- `/effort medium` pour le travail normal.
- `/effort high` pour la conception.
- `MAX_THINKING_TOKENS` (variable d'environnement) plafonne le budget de
  raisonnement **sur les modèles à budget fixe** ; les modèles à raisonnement
  adaptatif l'ignorent — pour eux, on ne règle que l'effort.

## Le cas particulier : un seul modèle

Beaucoup de postes passent par une passerelle qui **ne propose qu'un seul
modèle**. Dans ce cas, les trois alias (`ANTHROPIC_DEFAULT_OPUS_MODEL`,
`…_SONNET_MODEL`, `…_HAIKU_MODEL`) pointent vers le même nom, et le routage
par modèle est **inactif** : il n'y a qu'un seul prix.

Le vérifier :

```bash
python3 - <<'EOF'
import json, os, pathlib
p = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home()/".claude"))/"settings.json"
env = json.loads(p.read_text()).get("env", {}) if p.exists() else {}
alias = {k: env.get(k) for k in ("ANTHROPIC_DEFAULT_OPUS_MODEL","ANTHROPIC_DEFAULT_SONNET_MODEL","ANTHROPIC_DEFAULT_HAIKU_MODEL")}
print(alias)
print("routage actif" if len(set(alias.values())) > 1 else "un seul modèle : le routage est inactif")
EOF
```

Quand c'est le cas, **ne perds pas de temps à optimiser le modèle** : les
leviers réels sont le contexte et l'effort. Et l'**effort reste réglable
par modèle** dans `modelSettings` :

```json
{
  "modelSettings": {
    "ton-modele-unique": { "effortLevel": "medium" }
  }
}
```

## Les sous-agents

Un sous-agent a **son propre contexte** : ce qu'il rend ne revient à la
conversation principale que par son résumé. Deux règles :

1. **Le modèle se déclare dans l'agent** (`model: haiku` dans son
   frontmatter). Un sous-agent qui lit n'a pas besoin du modèle lourd.
2. **Le résumé est plafonné.** C'est la règle la plus importante : un
   sous-agent qui rend sa sortie brute **paie deux fois** — son contexte et
   celui de la conversation principale.

Les agents de ce dépôt (`lecteur`, `testeur`, `reviseur`) appliquent les
deux.

## Le réflexe qui manque

Le seul réflexe qui compte, et qu'aucun réglage ne remplace :

> **Une session = un chantier.**

Trois chantiers dans une session, c'est trois chantiers qui se paient
mutuellement en contexte. Le `/clear` entre deux tâches est **gratuit** ;
c'est le geste le plus rentable de tout l'outillage.

## Ce qu'il ne faut pas faire

- **Baisser le modèle pour rien.** Un modèle léger sur une tâche de
  conception coûte plus cher (en tours) qu'un modèle lourd sur une tâche
  mécanique.
- **Croire que `max` aide toujours.** L'effort élevé augmente la qualité
  **quand le problème est difficile**. Sur une tâche claire, il ajoute des
  jetons et rien d'autre.
- **Fixer un modèle par défaut « pour faire economies ».** Le bon modèle est
  celui de la tâche en cours ; le changement se fait avec `/model`.
