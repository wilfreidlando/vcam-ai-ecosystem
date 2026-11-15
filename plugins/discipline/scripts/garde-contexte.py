#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
garde-contexte.py — hook UserPromptSubmit.

Le coût d'une session n'est pas le travail : c'est la **relecture**. À
chaque tour, toute la conversation est renvoyée au modèle. Une session
devenue grosse coûte donc son prix à chaque aller-retour, jusqu'à la
compaction — et la compaction est elle-même une grosse requête.

Ce hook regarde la taille réelle du contexte **avant** le tour et, quand
elle dépasse le seuil, rappelle la chose qui coûte vraiment : `/clear`
(gratuit) plutôt que `/compact` (cher).

Il ne parle qu'une fois par tour utilisateur : une ligne, pas un discours.
Le but est de faire changer une habitude, pas de'Noisifier.

Entrée : le JSON de l'évènement de hook (avec `transcript_path`).
Sortie : `additionalContext` (une ligne) ou `{}`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Au-delà de ce remplissage, on parle.
SEUIL = 55
# Au-delà de celui-là, on parle plus fort.
SEUIL_FORT = 80

# On ne lit que la fin du transcript : les derniers usage suffisent.
TAILLE_LUE = 400_000


def dernier_contexte(transcript: Path):
    """(tokens du contexte, tokens écrits par le dernier tour) ou None."""
    try:
        size = transcript.stat().st_size
        with transcript.open("rb") as handle:
            if size > TAILLE_LUE:
                handle.seek(size - TAILLE_LUE)
                handle.readline()  # ligne tronquée : on la jette
            tail = handle.read().decode("utf-8", errors="ignore")
    except OSError:
        return None

    for line in reversed(tail.splitlines()):
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("type") != "assistant":
            continue
        usage = ((entry.get("message") or {}).get("usage")) or {}
        if not usage:
            continue
        contexte = (
            (usage.get("input_tokens") or 0)
            + (usage.get("cache_read_input_tokens") or 0)
            + (usage.get("cache_creation_input_tokens") or 0)
        )
        return contexte, (usage.get("output_tokens") or 0)
    return None


def fenetre() -> int:
    """La fenêtre de compaction en vigueur."""
    for nom in ("CLAUDE_CODE_AUTO_COMPACT_WINDOW",):
        valeur = os.environ.get(nom)
        if valeur and valeur.isdigit():
            return int(valeur)
    return 200_000


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print("{}")
        return 0

    brut = payload.get("transcript_path") or ""
    if not brut:
        print("{}")
        return 0

    mesure = dernier_contexte(Path(brut))
    if mesure is None:
        print("{}")
        return 0

    contexte, ecrits = mesure
    fenetre_ = fenetre()
    if not fenetre_:
        print("{}")
        return 0

    ratio = contexte * 100 / fenetre_
    if ratio < SEUIL:
        print("{}")
        return 0

    if ratio >= SEUIL_FORT:
        message = (
            f"⚠ Contexte à {ratio:.0f} % de la fenêtre ({contexte // 1000} k). "
            f"Chaque tour relit tout ce contexte. Si la tâche en cours est terminée, "
            f"/clear — c'est gratuit, alors que /compact coûte une grosse requête. "
            f"Si elle ne l'est pas, termine-la en une session courte : "
            f"relis 200 k à chaque tour coûte plus que le travail lui-même."
        )
    else:
        message = (
            f"Contexte à {ratio:.0f} % ({contexte // 1000} k). "
            f"Pense à /clear entre deux tâches sans lien — c'est gratuit."
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": message,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
