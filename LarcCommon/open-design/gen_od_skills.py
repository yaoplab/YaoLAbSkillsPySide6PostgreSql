"""Génère le dossier .od-skills — tout le savoir agent en un seul endroit.

Usage:
    python open-design/gen_od_skills.py
"""

from pathlib import Path
import shutil
import json
import re

ROOT = Path(__file__).parent
OD = ROOT / ".od-skills"

if OD.exists():
    shutil.rmtree(OD)
OD.mkdir()

# 1. Contexte
for f in ["CONTEXT.md", "AGENTS.md"]:
    src = ROOT / f
    if src.exists():
        shutil.copy(src, OD / f)

# 2. Skills (y compris INDEX.md)
dst_skills = OD / "skills"
shutil.copytree(ROOT / "skills", dst_skills)

# 3. Agents
if (ROOT / "agents").exists():
    shutil.copytree(ROOT / "agents", OD / "agents")

# 4. Parse frontmatter des skills pour générer l'index
skill_index = {}
for skill_dir in sorted(dst_skills.iterdir()):
    if not skill_dir.is_dir():
        continue
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        continue

    content = skill_md.read_text(encoding="utf-8")
    # Extrait le YAML frontmatter (entre --- et ---)
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        continue

    fm = {}
    for line in fm_match.group(1).strip().split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # Parse listes simples [a, b, c]
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(',') if v.strip()]
            fm[key] = val

    skill_index[skill_dir.name] = fm

# 5. Générer le README avec index dynamique
readme_lines = [
    "# Larc — Base de Connaissances Agent",
    "",
    "## Ordre de lecture pour un sub-agent",
    "",
    "1. `CONTEXT.md` — Contexte du projet",
    "2. `AGENTS.md` — Conventions générales",
    "3. `skills/INDEX.md` — Index des skills",
    "4. `skills/<nom>/SKILL.md` — Skill correspondant au module analysé",
    "",
    "## Skills disponibles",
    "",
    "| Skill | Priorité | Catégorie | Linter(s) |",
    "|---|---|---|---|",
]

for name, meta in sorted(skill_index.items()):
    priority = meta.get('priority', '—')
    category = meta.get('category', '—')
    linters = meta.get('linters', [])
    linter_str = ', '.join(linters) if linters else '—'
    readme_lines.append(f"| [{name}](skills/{name}/SKILL.md) | {priority} | {category} | {linter_str} |")

readme_lines += [
    "",
    "## Agents reviewers",
    "",
    "| Agent | Skills couverts |",
    "|---|---|",
]

agents_dir = OD / "agents"
if agents_dir.exists():
    for agent_file in sorted(agents_dir.glob("*.md")):
        name = agent_file.stem
        readme_lines.append(f"| [{name}](agents/{agent_file.name}) | Voir le fichier agent |")

readme_lines += [
    "",
    "## Structure",
    "",
    "| Dossier | Contenu |",
    "|---|---|",
    "| `skills/` | Skills (1 par fonctionnalité) |",
    "| `agents/` | Agents reviewers |",
    "",
    "## Règle absolue",
    "",
    "**Lire ce dossier AVANT d'analyser. Ne jamais modifier les fichiers du projet.**",
]

(OD / "README.md").write_text('\n'.join(readme_lines), encoding="utf-8")

print(f".od-skills/ généré ({len(skill_index)} skills) :")
for item in sorted(OD.rglob("*")):
    if item.is_file():
        print(f"  {item.relative_to(OD)}")
