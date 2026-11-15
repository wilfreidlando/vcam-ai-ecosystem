#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tronque-sortie.py — hook PreToolUse sur Bash.

Quand une commande est un **lanceur de tests**, sa sortie est MSEILLÉE :
cent lignes d'échec valent, mais trente mille lignes de journal non.

Pourquoi c'est un levier de coût, et pas un confort : ce qui entre dans le
contexte est **renvoyé à chaque tour suivant**. Cent kilo-octets de sortie
de test, dans une session de deux cents tours, c'est vingt millions de
jetons — pour une information qu'un résumé de dix lignes portait.

Le motif est celui de la documentation officielle, étendu aux lanceurs
usuels (pest, phpunit, jest, pytest, go test, cargo test, mvn, gradle).

Le code de sortie est **préservé** : un test qui échoue doit continuer à
échouer, sinon le garde-fou perd ses dents.

Entrée : le JSON de l'évènement de hook sur l'entrée standard.
Sortie : `updatedInput` avec la commande réécrite, ou `{}` pour ne rien changer.
"""

from __future__ import annotations

import json
import re
import sys

# Lignes conservées : assez pour voir le résumé d'un échec, pas assez pour
# noyer le contexte.
KEEP_LINES = 120

# Les lanceurs reconnus, en **position de commande** : début de ligne, ou
# après un `docker compose exec …`, un `env …`, un chemin, etc. — pour ne
# pas confondre un `grep pest` avec un lancement de tests.
RUNNERS = re.compile(
    r"""^\s*\(?\s*"""
    r"""(?:docker\s+compose\s+exec\s+(?:-[A-Za-z]+\s+)*(?:\S+\s+)*)?"""
    r"""(?:env\s+\S+\s+)*"""
    r"""(?:[\w./-]*/)?(?:vendor/bin/)?"""
    r"""(?:pest|phpunit|jest|vitest|pytest|py\.test|go\s+test|cargo\s+test|mvn|gradle|rspec|npm\s+test|pnpm\s+test|yarn\s+test)\b""",
    re.IGNORECASE,
)

# On ne touche pas une commande qui filtre déjà elle-même.
ALREADY_FILTERED = re.compile(r"\|\s*(tail|head|grep|awk|sed|rg)\b")


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

    if not RUNNERS.match(command) or ALREADY_FILTERED.search(command):
        print("{}")
        return 0

    # On garde le code de sortie du test, malgré le `tail` : sans cela, un
    # échec passe pour un succès et le garde-fou s'endort.
    filtered = (
        f"({command}) 2>&1 | tail -n {KEEP_LINES} ; "
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
