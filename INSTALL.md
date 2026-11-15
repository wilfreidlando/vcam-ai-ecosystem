# Installation

Pour un poste qui a le même problème : des sessions qui coûtent trop, et un
tableau de bord qui ne dit pas pourquoi.

## Ce qu'il faut

- **Claude Code** installé (le plugin, les hooks et la barre d'état sont des
  fonctions de Claude Code).
- **python3** — c'est tout. Ni `jq`, ni `node`, ni compte à créer.
- Aucun secret n'est demandé, aucun envoi réseau n'est fait par
  l'installateur.

## Poser les outils et les réglages

```bash
git clone <url-de-ce-dépôt> ~/vcam-ai-ecosystem
cd ~/vcam-ai-ecosystem
./install.sh --dry-run     # regardez d'abord ce qu'il ferait
./install.sh               # puis, pour de vrai
```

`--dry-run` montre exactement les clés ajoutées et celles qui existent déjà.
Sans lui, l'installateur :

- copie `ctx-cost` et `barre-etat` dans `~/.local/bin` ;
- **sauvegarde** `~/.claude/settings.json` en `settings.json.bak` ;
- **ajoute** les clés absentes : `statusLine`, `bashOutputMaxChars`,
  `crossSessionInbound`, `idleCompaction` ;
- **rapporte** celles qui existent déjà et **ne les touche pas** — en
  particulier `env.CLAUDE_CODE_AUTO_COMPACT_WINDOW`, qui est le levier le
  plus fort et qui mérite une décision humaine.

> Si `~/.local/bin` n'est pas dans le `PATH`, ajoutez-le :
> `export PATH="$HOME/.local/bin:$PATH"` (dans votre `~/.bashrc`).

## Poser le plugin

Dans Claude Code :

```
/plugin marketplace add ~/vcam-ai-ecosystem
/plugin install discipline@vcam-ecosystem
```

Puis **redémarrez la session** : les hooks et la barre d'état se chargent au
démarrage.

### Si la commande `/plugin` répond « isn't available in this environment »

C'est ce que répond l'extension VS Code. Le binaire de Claude Code, lui, est
livré **avec l'extension** : on l'appelle directement.

```bash
# le binaire, tel qu'il est posé par l'extension
CLAUDE=~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude

"$CLAUDE" plugin marketplace add https://github.com/wilfreidlando/vcam-ai-ecosystem
"$CLAUDE" plugin install discipline@vcam-ecosystem
"$CLAUDE" plugin list          # pour vérifier
```

Si vous avez la CLI `claude` dans le `PATH`, remplacez le chemin par
`claude` — les commandes sont les mêmes.

### Pour que d'autres personnes en profitent

Poussez ce dépôt sur un git, puis remplacez l'URL dans la première commande.
C'est tout : le dépôt est une marketplace, le plugin s'installe comme les
autres.

## Reprendre les règles d'engagement

L'outillage fait gagner des jetons ; il reste une **méthode**. Le dépôt
fournit un fichier prêt à l'emploi : `templates/CLAUDE.md`.

```bash
cp templates/CLAUDE.md ~/.claude/CLAUDE.md     # portée utilisateur, tous les dépôts
# ou
cp templates/CLAUDE.md /chemin/vers/un/depot/CLAUDE.md   # portée projet
```

Il dit en trois règles ce qui change la facture : `/clear` entre deux
chantiers non liés, déléguer la lecture et les tests aux agents légers, et
ne jamais ramener une sortie brute dans la conversation principale.

## Vérifier que ça marche

1. **La barre d'état** doit apparaître sous l'invite : modèle, branche,
   pourcentage de contexte, coût. Si elle est absente, le `statusLine` n'a
   pas été pris en compte — vérifiez que `~/.local/bin/barre-etat` est
   exécutable.
2. **Un test** doit être tronqué à 120 lignes :

   ```
   docker compose exec -T app vendor/bin/pest --parallel
   ```

   La commande exécutée devient
   `(... vendor/bin/pest --parallel) 2>&1 | tail -n 120 ; exit ${PIPESTATUS[0]}`.
3. **`/cout`** doit afficher le rapport du jour.
4. **L'inventaire** doit annoncer les trois agents :

   ```bash
   claude plugin details discipline@vcam-ecosystem
   # Agents (3)  testeur, reviseur, lecteur
   ```

   S'il affiche `Agents (0)`, voir `docs/PLUGIN.md` — c'est le piège qui ne
   dit rien.

## Si quelque chose ne va pas

| Symptôme | Cause | Solution |
|---|---|---|
| Pas de barre d'état | `statusLine` non pris en compte | `~/.claude/settings.json` → `statusLine` ; puis redémarrer |
| `ctx-cost : commande introuvable` | `~/.local/bin` absent du `PATH` | l'ajouter, puis `hash -r` |
| Le test échoue alors qu'il devrait passer | le code de sortie a été perdu | le hook le préserve (`exit ${PIPESTATUS[0]}`) ; vérifier que `bash` est bien le shell |
| Le hook ne se déclenche pas | plugin non chargé | `/plugin` pour voir l'état ; redémarrer la session |

## Désinstaller

```bash
./install.sh --uninstall
```

Les outils posés sont retirés. Les réglages de `~/.claude/settings.json` sont
**laissés en place** : ils sont supprimés à la main si vous le voulez — c'est
votre configuration, pas la nôtre.

## Et ensuite ?

- `docs/MESURES.md` — la baseline mesurée et la méthode.
- `docs/POLITIQUE-MODELES.md` — le routage par tâche.
- `docs/PLUGIN.md` — le plugin et ses trois pièges silencieux.
- Le skill `session-courte` — les cinq gestes, classés par rendement.
