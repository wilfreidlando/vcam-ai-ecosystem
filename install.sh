#!/usr/bin/env bash
# install.sh — poser l'écosystème sur un poste.
#
# Ce script ne détruit rien : il ne remplace AUCUNE clé de configuration
# existante. Il n'ajoute que les clés absentes, et il **rapporte** celles
# qui existent déjà avec une valeur différente — le choix reste à
# l'humain, parce que la configuration d'un poste est sa décision.
#
# Usage :
#   ./install.sh                     # pose les outils, propose les réglages
#   ./install.sh --url <git-url>     # enregistre aussi la marketplace
#   ./install.sh --dry-run           # montre ce qui serait fait
#   ./install.sh --uninstall         # retire les outils posés

set -uo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${HOME}/.local/bin"
SETTINGS="${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/settings.json"
DRY=0
URL=""
UNINSTALL=0

while [ $# -gt 0 ]; do
  case "$1" in
    --url) URL="${2:-}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "option inconnue : $1" >&2; exit 2 ;;
  esac
done

say()  { printf '  %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }

# ── désinstallation ────────────────────────────────────────────────────────
if [ "$UNINSTALL" -eq 1 ]; then
  step "Retrait"
  for outil in ctx-cost barre-etat; do
    if [ -e "${BIN}/${outil}" ]; then rm -f "${BIN}/${outil}"; ok "retiré : ${outil}"; fi
  done
  say "Les réglages de ~/.claude/settings.json sont laissés en place (retire-les à la main si tu veux)."
  exit 0
fi

# ── prérequis ──────────────────────────────────────────────────────────────
step "Prérequis"
command -v python3 >/dev/null 2>&1 && ok "python3 $(python3 --version 2>&1 | cut -d' ' -f2)" || bad "python3 est requis (jq n'est pas nécessaire)"
command -v claude   >/dev/null 2>&1 && ok "claude $(claude --version 2>/dev/null | head -1)" || warn "claude-code n'est pas dans le PATH"
[ -d "${HOME}/.claude" ] && ok "~/.claude existe" || warn "~/.claude est absent : les réglages seront créés"

# ── outils ─────────────────────────────────────────────────────────────────
step "Outils"
mkdir -p "$BIN" 2>/dev/null || true
for outil in ctx-cost barre-etat; do
  src="${RACINE}/tools/${outil}.py"
  if [ -f "$src" ]; then
    if [ "$DRY" -eq 1 ]; then
      say "installerait ${BIN}/${outil}"
    else
      install -m 0755 "$src" "${BIN}/${outil}" && ok "${BIN}/${outil}"
    fi
  fi
done
if [ "$DRY" -eq 0 ]; then
  case ":${PATH}:" in
    *":${BIN}:"*) ;;
    *) warn "${BIN} n'est pas dans le PATH — ajoute-le pour utiliser ctx-cost et barre-etat" ;;
  esac
fi

# ── réglages ───────────────────────────────────────────────────────────────
step "Réglages de ~/.claude/settings.json"
python3 - "$SETTINGS" "$DRY" "$URL" <<'PYTHON'
import json
import shutil
import sys
from pathlib import Path

chemin = Path(sys.argv[1])
dry = sys.argv[2] == "1"
url = sys.argv[3]

# Les réglages que l'on **ajoute** s'ils sont absents.
# Justification de chacun : c'est le prix, en contexte, de ne pas les avoir.
AJOUTS = {
    # La barre d'état : le remplissage du contexte, visible AVANT qu'il ne
    # coûte. C'est le levier qui change une habitude.
    "statusLine": {
        "type": "command",
        "command": "python3 ${HOME}/.local/bin/barre-etat",
    },
    # Toute la sortie d'une commande entre dans le contexte, et y reste,
    # relue à chaque tour. 20 k suffisent à voir un échec ; au-delà, on paie
    # pour du journal.
    "bashOutputMaxChars": 20000,
    # Un message venu d'une AUTRE session, delivered, est un tour complet
    # qui renvoie tout le contexte. En « hold », il attend.
    "crossSessionInbound": "hold",
    # Compacter pendant qu'on est absent coûte une grosse requête pour rien.
    "idleCompaction": False,
}

RECOMMANDES = {
    # La fenêtre de compaction : 200 k au lieu de 500 k. On compacte plus
    # tôt, donc on relit moins longtemps.
    "env.CLAUDE_CODE_AUTO_COMPACT_WINDOW": "196608",
}

if not chemin.exists():
    print(f"  · {chemin} n'existe pas encore : il sera créé au premier lancement de claude")
    data = {}
else:
    try:
        data = json.loads(chemin.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  ✗ {chemin} est illisible ({exc}) : je n'y touche pas")
        sys.exit(0)

appliques, rapportes = [], []

for cle, valeur in AJOUTS.items():
    if cle in data:
        rapportes.append((cle, data[cle]))
    else:
        data[cle] = valeur
        appliques.append(cle)

# Les réglages recommandés : on ne touche à rien si la clé existe.
env = data.setdefault("env", {})
for cle, valeur in RECOMMANDES.items():
    court = cle.split(".")[-1]
    if court in env:
        rapportes.append((f"env.{court}", env[court]))
    else:
        env[court] = valeur
        appliques.append(f"env.{court}")

if url:
    marketplaces = data.setdefault("extraKnownMarketplaces", {})
    if "vcam-ecosystem" not in marketplaces:
        marketplaces["vcam-ecosystem"] = {"source": {"source": "git", "url": url}}
        appliques.append("extraKnownMarketplaces.vcam-ecosystem")

if dry:
    print(f"  (simulation — {chemin} non modifié)")
    for cle in appliques:
        print(f"  + ajouterait {cle}")
    for cle, valeur in rapportes:
        print(f"  · {cle} existe déjà : {json.dumps(valeur, ensure_ascii=False)[:80]}")
    sys.exit(0)

if not appliques:
    print("  · rien à ajouter : tout est déjà en place")
else:
    sauvegarde = chemin.with_suffix(".json.bak")
    shutil.copy2(chemin, sauvegarde)
    chemin.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"  ✓ {len(appliques)} réglage(s) ajouté(s) — sauvegarde : {sauvegarde.name}")
    for cle in appliques:
        print(f"      + {cle}")

for cle, valeur in rapportes:
    print(f"  · {cle} existe déjà ({json.dumps(valeur, ensure_ascii=False)[:60]}) : je n'y touche pas")
PYTHON

# ── marketplace et plugin ──────────────────────────────────────────────────
step "Le plugin"
cat <<EOF

  1. Enregistre la marketplace (une seule fois) :

       /plugin marketplace add ${URL:-<url-git-de-ce-dépôt>}

     ou, si tu as cloné ce dépôt en local :

       /plugin marketplace add ${RACINE}

  2. Installe le plugin :

       /plugin install discipline@vcam-ecosystem

  3. Redémarre la session (les hooks et la barre d'état se chargent au
     démarrage).

EOF

step "Vérification"
if [ "$DRY" -eq 0 ] && [ -x "${BIN}/ctx-cost" ]; then
  "${BIN}/ctx-cost" --day "$(date +%F)" 2>/dev/null | head -12 || say "ctx-cost n'a rien trouvé (aucune session aujourd'hui)"
fi

cat <<EOF

  Ce qui change, concrètement :
    · la barre d'état montre le remplissage du contexte et son coût ;
    · les sorties de tests sont tronquées à 120 lignes (code de sortie intact) ;
    · au-delà de 55 % de contexte, un rappel : /clear est gratuit ;
    · /fin, /cout, /handoff et /modele sont disponibles ;
    · les sous-agents lecteur, testeur et reviseur rendent des résumés courts.

  Pour désinstaller : ./install.sh --uninstall

EOF
