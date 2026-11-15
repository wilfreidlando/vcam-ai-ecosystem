# Le plugin : comment il est fait, et les pièges que Claude Code ne dit pas

Ce dépôt est une **marketplace** (`.claude-plugin/marketplace.json`) qui
contient un plugin (`plugins/discipline/`). Trois choses le font marcher, et
chacune peut échouer **silencieusement** : l'inventaire affiche alors un
composant à zéro, sans message d'erreur.

## La structure

```
.claude-plugin/marketplace.json      ← le catalogue : nom, source, version
plugins/discipline/
  .claude-plugin/plugin.json         ← la fiche du plugin
  skills/session-courte/SKILL.md     ← un skill (chargé à la demande)
  commands/{fin,cout,handoff,modele}.md   ← des commandes (exposées en skills)
  agents/{lecteur,testeur,reviseur}.md     ← des sous-agents
  hooks/hooks.json                   ← les crochets
  scripts/*.py                       ← les scripts que les crochets lancent
```

## Les trois pièges

### 1. Ne déclarez pas les agents

`plugin.json` accepte une clé `agents`, mais **la remplir casse le
chargement** : l'inventaire affiche `Agents (0)` alors que les fichiers sont
présents et valides.

La bonne façon est de **ne rien écrire** : le dossier `agents/` est découvert
tout seul, comme le fait la marketplace ECC.

> Piège voisin : le validateur refuse `"./agents/"` (un dossier) et exige
> `"./agents/xxx.md"`. On passe donc par la découverte, qui n'exige rien.

Vérification :

```bash
claude plugin details discipline@vcam-ecosystem
#   Skills (5)  cout, fin, handoff, modele, session-courte
#   Agents (3)  testeur, reviseur, lecteur
#   Hooks (2)   PreToolUse, UserPromptSubmit
```

### 2. Un nom d'outil faux fait tomber l'agent entier

Dans le frontmatter d'un agent, `tools:` n'accepte que des outils
existants. `LS` n'existe pas dans Claude Code : l'agent qui le portait
n'apparaissait dans aucun inventaire, sans avertissement.

Les outils qui existent : `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`,
`WebFetch`, `WebSearch`, `Task`, `NotebookEdit`, `TodoWrite`, `SlashCommand`,
`AskUserQuestion`, `Skill`…

### 3. Changer le code ne suffit pas : changez la version

`claude plugin update` compare les **versions**, pas les contenus. Un
correctif poussé sur `main` sans bump de version n'est jamais recopié dans le
cache : le plugin installé reste l'ancien, silencieusement.

```bash
# 1. corriger
# 2. versionner
sed -i 's/"version": "1.0.2"/"version": "1.0.3"/' \
    plugins/discipline/.claude-plugin/plugin.json .claude-plugin/marketplace.json
# 3. pousser, puis
claude plugin marketplace update vcam-ecosystem
claude plugin update discipline@vcam-ecosystem
```

## Le protocole des crochets

Les deux crochets parlent le protocole officiel, tel quel :

**PreToolUse** — réécrire la commande d'un lanceur de tests pour n'en garder
que 120 lignes, en préservant le code de sortie :

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "updatedInput": { "command": "(...) 2>&1 | tail -n 120 ; exit ${PIPESTATUS[0]}" }
  }
}
```

Deux étages, parce que deux besoins :

| Famille | Gardé | Couvrant |
|---|---|---|
| Lanceurs de tests | **120 lignes** | pest, phpunit, jest, vitest, pytest, go test, cargo test, mvn, gradle, rspec, npm test… |
| Journaux | **400 lignes** | `docker compose logs`, `docker build`, `npm ci`, `composer install`, `make`, `git log -p` |

Ce qui n'est **pas** tronqué, et pourquoi :

- `cat`, `head`, `tail` — **lire un fichier doit rester complet**. Une
  troncature ici ferait écrire du code à partir d'un fichier tronqué. Le
  harnais plafonne déjà toute sortie à `bashOutputMaxChars`.
- `git diff`, `git show` — le diff du travail en cours est le matériau de la
  revue ; il doit arriver entier.
- `git log` déjà borné (`-n`, `--oneline`, `--stat`) — le volume est
  maîtrisé.

**UserPromptSubmit** — injecter **une ligne** quand le contexte dépasse 55 %
de la fenêtre de compaction :

```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Contexte à 61 % (118 k). Pense à /clear entre deux tâches sans lien — c'est gratuit."
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` donne le chemin du plugin installé : c'est ainsi que
les scripts sont trouvés, quelle que soit la place du cache.

## Ce que ça coûte

L'inventaire dit le chiffre exact :

```
Always-on: ~467 tok   ajoutés à chaque session
```

C'est le prix du plugin : les crochets, eux, ne coûtent **aucun jeton**
(« harness-only »). Le nombre à surveiller est celui du saut de contexte — il
est imprimé par `claude plugin details`.
