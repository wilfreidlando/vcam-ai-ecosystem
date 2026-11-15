#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tronque-sortie.py — hook PreToolUse sur Bash.

Quand une commande produit un **journal**, sa sortie est MSEILLÉE : cent
lignes d'échec valent, mais trente mille lignes de journal non.

Pourquoi c'est un levier de coût, et pas un confort : ce qui entre dans le
contexte est **renvoyé à chaque tour suivant**. Cent kilo-octets de sortie
de test, dans une session de deux cents tours, c'est vingt millions de
jetons — pour une information qu'un résumé de dix lignes portait.

Deux étages de troncature, parce que deux besoins :

  * les **lanceurs de tests** — 120 lignes suffisent à lire un échec ;
  * les **journaux** (logs de conteneur, installation, compilation,
    historique des commits) — 400 lignes, car ils racontent parfois
    plusieurs choses à la fois.

Ce qui n'est **pas** tronqué, et pourquoi :

  * `cat`, `head`, `tail` — lire un fichier doit rester **complet**. Une
    troncature ici ferait écrire du code à partir d'un fichier tronqué ;
    c'est le risque exact qu'on ne prend pas. Le harnais plafonne déjà
    toute sortie à `bashOutputMaxChars`.
  * `git diff`, `git show` — le diff du travail en cours est le matériau
    de la revue ; il doit arriver entier.

Le code de sortie est **préservé** : un test qui échoue doit continuer à
échouer, sinon le garde-fou perd ses dents.

Entrée : le JSON de l'évènement de hook sur l'entrée standard.
Sortie : `updatedInput` avec la commande réécrite, ou `{}` pour ne rien changer.
"""

from __future__ import annotations

import json
import re
import sys

# Lignes conservées pour un lanceur de tests : assez pour voir le résumé
# d'un échec, pas assez pour noyer le contexte.
KEEP_TESTS = 120
# Lignes conservées pour un journal : logs, installation, compilation.
KEEP_JOURNAL = 400

# Les lanceurs de tests, en **position de commande** : début de ligne, ou
# après un `docker compose exec …`, un `env …`, un chemin, etc. — pour ne
# pas confondre un `grep pest` avec un lancement de tests.
TESTS = re.compile(
    r"""^\s*\(?\s*"""
    r"""(?:docker\s+compose\s+exec\s+(?:-[A-Za-z]+\s+)*(?:\S+\s+)*)?"""
    r"""(?:env\s+\S+\s+)*"""
    r"""(?:[\w./-]*/)?(?:vendor/bin/)?"""
    r"""(?:pest|phpunit|jest|vitest|pytest|py\.test|go\s+test|cargo\s+test|mvn|gradle|rspec|npm\s+test|pnpm\s+test|yarn\s+test)\b""",
    re.IGNORECASE,
)

# Les journaux : ils racontent une installation, une compilation, un conteneur
# ou l'historique. On en garde assez pour comprendre, pas assez pour noyer.
JOURNAL = re.compile(
    r"""^\s*\(?\s*"""
    r"""(?:"""
    r"""docker\s+compose\s+(?:logs|build|pull|up\s+--build)\b"""
    r"""|docker\s+(?:logs|build|pull)\b"""
    r"""|docker\s+compose\s+exec\s+(?:-[A-Za-z]+\s+)*(?:\S+\s+)*"""
    r"""(?:composer\s+(?:install|update|dump-autoload)|npm\s+(?:ci|install|i|run\s+build)"""
    r"""|yarn\s+(?:install|add|build)|pnpm\s+(?:install|add|build)"""
    r"""|make(?:\s+\S+)*)"""
    r"""|composer\s+(?:install|update|dump-autoload)"""
    r"""|npm\s+(?:ci|install|i|run\s+build)"""
    r"""|yarn\s+(?:install|add|build)|pnpm\s+(?:install|add|build)"""
    r"""|make(?:\s+\S+)*"""
    r"""|git\s+log\b"""
    r""")\b""",
    re.IGNORECASE,
)

# On ne touche pas une commande qui filtre déjà elle-même.
ALREADY_FILTERED = re.compile(r"\|\s*(tail|head|grep|awk|sed|rg)\b")

# `git log` SANS limite : le patch peut faire des milliers de lignes.
# (Si l'historique est déjà borné — `-n`, `--oneline`, `--stat` — on n'y
# touche pas : le volume est déjà maîtrisé.)
GIT_LOG_SANS_LIMITE = re.compile(
    r"git\s+log\b(?![^|;&]*(?:-n\s*\d|--max-count|--oneline|--stat))", re.IGNORECASE
)


def garder(command: str) -> int | None:
    """Le nombre de lignes à garder, ou None si la commande est intacte."""
    if ALREADY_FILTERED.search(command):
        return None
    if TESTS.match(command):
        return KEEP_TESTS
    if JOURNAL.match(command):
        # `git log` déjà borné, ou sans patch : on n'y touche pas.
        if command.lstrip().lower().startswith("git log") and not GIT_LOG_SANS_LIMITE.search(command):
            return None
        return KEEP_JOURNAL
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print("{}")
        return 0

    command = ((payload.get("tool_input") or {}).get("command")) or ""
    if not command:
        print("{}")
        return 0

    lignes = garder(command)
    if lignes is None:
        print("{}")
        return 0

    # On garde le code de sortie de la commande, malgré le `tail` : sans
    # cela, un échec passe pour un succès et le garde-fou s'endort.
    filtered = (
        f"({command}) 2>&1 | tail -n {lignes} ; "
        'exit ${PIPESTATUS[0]}'
    )

    tool_input = payload.get("tool_input") or {}
    tool_input["command"] = filtered

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": tool_input,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
