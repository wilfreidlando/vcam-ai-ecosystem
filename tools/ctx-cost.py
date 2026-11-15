#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ctx-cost.py — où sont partis mes jetons ?

Un tableau de bord qui ne se contente pas de compter : il **explique**.

Le premier réflexe, en voyant « 257 M de jetons », est de croire qu'une
intelligence a beaucoup travaillé. C'est faux dans la quasi-totalité des cas :
le coût d'une session est presque entièrement le **relecture de la
conversation**, pas l'écriture. Cet outil mesure les deux séparément et
nomme la cause.

Trois questions, trois réponses :

  1. Combien de tours de modèle (aller-retours) la session a-t-elle coûtés ?
  2. Quel contexte moyen chaque tour a-t-il renvoyé ?
  3. Combien de jetons **écrits** (la vraie production) face aux jetons
     **relus** (la conversation réexpédiée) ?

Usage :
    ctx-cost.py                  # tous les jours, tous les projets
    ctx-cost.py --day AAAA-MM-JJ # un jour
    ctx-cost.py --json           # sortie machine
    ctx-cost.py --top 20         # les prompts les plus chers (défaut 10)

Lecture seule : il ne lit que les transcriptions locales, il n'écrit rien.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
PROJECTS_DIR = CLAUDE_DIR / "projects"

BAR_FULL = "█"
BAR_EMPTY = "░"


# ─────────────────────────────────────────────────────────────────────────────
# Lecture
# ─────────────────────────────────────────────────────────────────────────────

def iter_transcripts(root: Path):
    """Chaque fichier de transcription : session principale ou agent."""
    if not root.exists():
        return
    for path in root.rglob("*.jsonl"):
        yield path


def read_entries(path: Path):
    """Les entrées d'une transcription, en ignorant les lignes illisibles."""
    try:
        with path.open("r", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def usage_of(entry: dict):
    """Les compteurs d'une réponse de modèle, ou None."""
    if entry.get("type") != "assistant":
        return None
    message = entry.get("message") or {}
    usage = message.get("usage")
    if not isinstance(usage, dict):
        return None
    details = usage.get("output_tokens_details") or {}
    return {
        "input": usage.get("input_tokens") or 0,
        "cache_read": usage.get("cache_read_input_tokens") or 0,
        "cache_write": usage.get("cache_creation_input_tokens") or 0,
        "output": usage.get("output_tokens") or 0,
        "thinking": details.get("thinking_tokens") or 0,
    }


def is_real_prompt(entry: dict) -> bool:
    """Un vrai message de l'humain (pas un résultat d'outil, pas un rappel)."""
    if entry.get("type") != "user":
        return False
    if entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    message = entry.get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return any(
            isinstance(block, dict)
            and block.get("type") == "text"
            and (block.get("text") or "").strip()
            for block in content
        )
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Analyse
# ─────────────────────────────────────────────────────────────────────────────

class Bucket:
    """Un bilan (une journée, une session, un agent)."""

    def __init__(self):
        self.rounds = 0
        self.input = 0
        self.cache_read = 0
        self.cache_write = 0
        self.output = 0
        self.thinking = 0

    @property
    def written(self):
        """Ce que la session a réellement produit."""
        return self.output

    @property
    def reread(self):
        """Ce qui a été renvoyé au modèle sans être du travail neuf."""
        return self.cache_read + self.input

    @property
    def total(self):
        return self.input + self.cache_read + self.cache_write + self.output

    @property
    def avg_context(self):
        """Le contexte moyen renvoyé à chaque tour."""
        return int(self.reread / self.rounds) if self.rounds else 0

    @property
    def reread_ratio(self):
        return (self.reread / self.total * 100) if self.total else 0.0


def analyse(paths):
    days = defaultdict(Bucket)
    sessions = defaultdict(Bucket)
    agents = defaultdict(Bucket)
    expensive = []
    prompts = 0

    for path in paths:
        is_agent = "subagents" in path.parts
        current_prompt = None
        prompt_cost = defaultdict(int)
        prompt_turns = defaultdict(int)
        prompt_started = {}
        prompt_day = {}

        for entry in read_entries(path):
            day = (entry.get("timestamp") or "")[:10]

            if is_real_prompt(entry):
                prompts += 1
                current_prompt = entry.get("uuid") or f"p{prompts}"
                prompt_cost[current_prompt] = 0
                prompt_turns[current_prompt] = 0
                prompt_started[current_prompt] = entry.get("timestamp") or ""
                prompt_day[current_prompt] = day
                continue

            usage = usage_of(entry)
            if usage is None:
                continue

            total = usage["input"] + usage["cache_read"] + usage["cache_write"] + usage["output"]

            for bucket in (days[day],
                           sessions[entry.get("sessionId") or path.stem],
                           agents[path.stem] if is_agent else None):
                if bucket is None:
                    continue
                bucket.rounds += 1
                bucket.input += usage["input"]
                bucket.cache_read += usage["cache_read"]
                bucket.cache_write += usage["cache_write"]
                bucket.output += usage["output"]
                bucket.thinking += usage["thinking"]

            if current_prompt:
                prompt_cost[current_prompt] += total
                prompt_turns[current_prompt] += 1
                if prompt_cost[current_prompt] > 2_000_000:
                    expensive.append(
                        {
                            "day": prompt_day.get(current_prompt, day),
                            "started": prompt_started.get(current_prompt, ""),
                            "cost": prompt_cost[current_prompt],
                            "turns": prompt_turns[current_prompt],
                            "source": path.name,
                        }
                    )

    return days, sessions, agents, expensive, prompts


# ─────────────────────────────────────────────────────────────────────────────
# Rendu
# ─────────────────────────────────────────────────────────────────────────────

def human(n: float) -> str:
    for unit, size in (("G", 1_000_000_000), ("M", 1_000_000), ("k", 1_000)):
        if n >= size:
            return f"{n / size:.1f}{unit}"
    return f"{int(n)}"


def bar(ratio: float, width: int = 18) -> str:
    filled = max(0, min(width, int(round(ratio * width / 100))))
    return BAR_FULL * filled + BAR_EMPTY * (width - filled)


def verdict(b: Bucket) -> str:
    """Le diagnostic en une phrase."""
    if b.rounds == 0:
        return ""
    if b.reread_ratio >= 90:
        return "⟶ le coût est la RELECTURE de la conversation, pas le travail"
    if b.reread_ratio >= 70:
        return "⟶ la relecture domine encore ; le contexte est trop long"
    if b.avg_context > 120_000:
        return "⟶ contexte moyen élevé : des sessions plus courtes divisent le coût"
    return "⟶ répartition saine"


def print_report(days, agents, expensive, top=10, only_day=None):
    if not days:
        print("Aucune transcription trouvée dans", PROJECTS_DIR)
        return

    selected = {d: b for d, b in days.items() if only_day is None or d == only_day}
    if not selected:
        print(f"Aucune activité le {only_day}.")
        return

    print()
    print("  ctx-cost — où sont partis mes jetons")
    print("  " + "─" * 76)
    print(f"  {'jour':<12} {'tours':>6} {'ctx moyen':>10} {'écrit':>8} {'relu':>8} {'total':>8}  part relecture")
    print("  " + "─" * 76)

    for day in sorted(selected):
        b = selected[day]
        print(
            f"  {day:<12} {b.rounds:>6} {human(b.avg_context):>10} {human(b.written):>8}"
            f" {human(b.reread):>8} {human(b.total):>8}  {bar(b.reread_ratio)} {b.reread_ratio:5.1f}%"
        )

    print("  " + "─" * 76)
    total = sum(b.total for b in selected.values())
    written = sum(b.written for b in selected.values())
    reread = sum(b.reread for b in selected.values())
    rounds = sum(b.rounds for b in selected.values())
    busiest = max(selected, key=lambda d: selected[d].total)

    if total:
        print(
            f"  {'TOTAL':<12} {rounds:>6} {human(int(reread / rounds)) if rounds else '-':>10}"
            f" {human(written):>8} {human(reread):>8} {human(total):>8}"
        )
        print()
        print(f"  {verdict(selected[busiest])}")
        print(
            f"  Un tour coûte {human(selected[busiest].avg_context)} de contexte ; "
            f"l'écriture n'en est que {written / total * 100:.1f} %."
        )

    if agents:
        print()
        print("  Agents (chacun a son propre contexte) :")
        for name in sorted(agents, key=lambda n: agents[n].total, reverse=True)[:8]:
            a = agents[name]
            print(
                f"    …{name[-11:]:<13} {a.rounds:>5} tours  {human(a.total):>8}"
                f"  écrit {human(a.output):>7}  relu {human(a.reread):>8}  {a.reread_ratio:5.1f}% relecture"
            )

    if expensive:
        print()
        print(f"  Les {min(top, len(expensive))} prompts les plus chers — chacun a valu tous les tours qui l'ont suivi :")
        for item in sorted(expensive, key=lambda e: -e["cost"])[:top]:
            per_turn = item["cost"] // max(1, item["turns"])
            print(
                f"    {item['day']}  {human(item['cost']):>8}  {item['turns']:>4} tours"
                f"  ({human(per_turn)} par tour)  {item['source']}"
            )

    print()
    print("  Leviers, du plus rentable au moins rentable :")
    print("    1. /clear entre deux tâches non liées — c'est gratuit ; /compact coûte une grosse requête.")
    print("    2. Une session = un chantier. Une session longue relit 200 k à chaque tour.")
    print("    3. Baisser autoCompactWindow : mieux vaut compacter tôt que relire 200 k cinquante fois.")
    print("    4. Sous-agent : un modèle léger + un RÉSUMÉ en retour, jamais la sortie brute.")
    print("    5. Un hook qui tronque la sortie des tests : 100 k dans le contexte = 100 k à chaque tour.")
    print("    6. Des prompts précis : « améliore le code » déclenche un scan large.")
    print()
    return


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyser la consommation de jetons des sessions locales.")
    parser.add_argument("--day", help="ne montrer qu'un jour (AAAA-MM-JJ)")
    parser.add_argument("--top", type=int, default=10, help="combien de prompts chers montrer")
    parser.add_argument("--json", action="store_true", help="sortie machine")
    parser.add_argument("--dir", help="dossier de projets (défaut : ~/.claude/projects)")
    args = parser.parse_args()

    root = Path(args.dir) if args.dir else PROJECTS_DIR
    paths = list(iter_transcripts(root))
    if not paths:
        print(f"Aucune transcription sous {root}", file=sys.stderr)
        return 1

    days, sessions, agents, expensive, prompts = analyse(paths)

    if args.json:
        payload = {
            "days": {
                d: {
                    "rounds": b.rounds,
                    "avg_context": b.avg_context,
                    "written": b.written,
                    "reread": b.reread,
                    "total": b.total,
                    "reread_ratio": round(b.reread_ratio, 2),
                }
                for d, b in days.items()
            },
            "agents": {
                n: {"rounds": b.rounds, "total": b.total, "written": b.written, "reread": b.reread}
                for n, b in agents.items()
            },
            "prompts": prompts,
        }
        print(json.dumps(payload, indent=2))
        return 0

    print_report(days, agents, expensive, top=args.top, only_day=args.day)
    return 0


if __name__ == "__main__":
    sys.exit(main())
