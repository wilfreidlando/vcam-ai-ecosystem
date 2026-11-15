#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
barre-etat.py — la ligne d'état qui regarde le context avant qu'il ne coûte.

Claude Code passe un JSON sur l'entrée standard ; ce script en rend une
ligne. Il n'ajoute rien au coût : une seule exécution par tour d'affichage.

Ce qu'il montre, dans cet ordre :
  - le modèle et la branche ;
  - **le taux de remplissage du contexte** — c'est la seule chose qui
    predicts le coût du tour suivant ;
  - le coût de la session et sa durée ;
  - le taux de cache (la relecture).

Au-delà de 60 %, la ligne passe à l'orange et rappelle `/clear`. Au-delà de
80 %, elle passe au rouge : le prochain tour relira tout.

python3, et non jq : sur la machine du commanditaire, jq n'est pas installé.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

RESET = "\033[0m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"


def field(data, *path, default=None):
    for key in path:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
    return default if data is None else data


def git_branch(cwd: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if out.returncode == 0:
            branch = out.stdout.strip()
            dirty = subprocess.run(
                ["git", "-C", cwd, "status", "--porcelain"],
                capture_output=True, text=True, timeout=2,
            ).stdout.strip()
            return branch + ("*" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def human(n) -> str:
    n = float(n or 0)
    for unit, size in (("G", 1_000_000_000), ("M", 1_000_000), ("k", 1_000)):
        if n >= size:
            return f"{n / size:.1f}{unit}"
    return f"{int(n)}"


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    model = field(data, "model", "display_name", default="")
    workspace = field(data, "workspace", "current_dir", default=os.getcwd())
    branch = git_branch(workspace)

    pct = float(field(data, "context_window", "used_percentage", default=0) or 0)
    total_in = field(data, "context_window", "total_input_tokens", default=0) or 0
    cost = field(data, "cost", "total_cost_usd", default=0) or 0
    duration_ms = field(data, "total_duration_ms", default=0) or 0
    hit_ratio = field(data, "prompt_cache", "hit_ratio")
    warm = field(data, "prompt_cache", "warm")

    minutes = int(duration_ms / 60000)
    hours, minutes = divmod(minutes, 60)

    # ── la partie qui change de couleur : le contexte ─────────────────────
    if pct >= 80:
        colour, state = RED, "⚠"
    elif pct >= 60:
        colour, state = YELLOW, "!"
    else:
        colour, state = GREEN, ""

    width = 10
    filled = max(0, min(width, int(round(pct * width / 100))))
    bar = "█" * filled + "░" * (width - filled)

    parts = []
    if model:
        parts.append(f"{CYAN}{model}{RESET}")
    if branch:
        parts.append(f"{DIM}{branch}{RESET}")
    parts.append(f"{colour}{state} {bar} {pct:4.1f}%{RESET} {DIM}({human(total_in)}){RESET}")
    parts.append(f"{DIM}${cost:.2f}{RESET}" if cost else "")
    if hours:
        parts.append(f"{DIM}{hours}h{minutes:02d}{RESET}")
    elif minutes:
        parts.append(f"{DIM}{minutes}min{RESET}")
    if hit_ratio is not None:
        parts.append(f"{DIM}cache {float(hit_ratio) * 100:.0f}%{RESET}")
    if warm is False:
        parts.append(f"{YELLOW}froid{RESET}")

    line = " │ ".join(p for p in parts if p)

    # Au-delà de 60 %, on rappelle ce qui fait baisser le coût — pour de vrai.
    if pct >= 60:
        line += f"  {YELLOW}/clear pour repartir à zéro{RESET}"

    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
