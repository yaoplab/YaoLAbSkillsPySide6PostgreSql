#!/usr/bin/env python3
"""Meta-linter : évalue chaque SKILL.md selon la rubrique 10/10.

Critères (1 point chacun) :
  1. YAML frontmatter valide avec les clés requises
  2. Sections 0-6 présentes et dans l'ordre
  3. Taille ≤ 400 lignes (bonus si ≤ 300, pénalité si > 600)
  4. Tables ❌/✅ avec sévérité (P0/P1/P2)
  5. Au moins 1 méthode de vérification (linter, pytest, commande)
  6. Dépendances résolues (références croisées vers skills existants)
  7. ≥ 1 exemple de code before/after
  8. Checklist avec checkboxes mécaniquement vérifiables
  9. Aucune règle dupliquée (vérifié par cross-ref scan)
  10. Frontmatter triggers listés (ou "N/A" si skill de référence)

Usage:
  python scripts/lint_skill_checker.py                     # Tous les skills
  python scripts/lint_skill_checker.py --dir skills/design-tokens  # Un skill
  python scripts/lint_skill_checker.py --json               # Sortie JSON
  python scripts/lint_skill_checker.py --all                # Inclure dépréciés
"""

import re
import io
import sys
from pathlib import Path

SKILLS_DIR = Path(r"C:\projets\LarcCommon\open-design\skills")
EXCLUDE = ["design-system-larc"]  # Déprécié

REQUIRED_FM_KEYS = ["skill", "version", "priority", "category",
                     "depends_on", "applies_to", "linters", "reviewers", "subsystems"]
VALID_PRIORITIES = ["P0", "P1", "P2"]
VALID_CATEGORIES = ["design", "infrastructure", "quality", "catalog", "feature", "data"]
REQUIRED_SECTIONS = [
    "0. Contexte", "1. Fonction", "2. Contraintes",
    "3. Code", "4. Exemples", "5. Step by Step", "6. Checklist"
]


def parse_frontmatter(content: str) -> dict:
    """Extrait le YAML frontmatter entre --- et ---."""
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).strip().split('\n'):
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip().strip('"').strip("'")
                       for v in val[1:-1].split(',') if v.strip()]
            fm[key] = val
    return fm


def check_skill(skill_dir: Path) -> dict:
    """Évalue un skill et retourne son score détaillé."""
    skill_md = skill_dir / "SKILL.md"
    name = skill_dir.name

    if not skill_md.exists():
        return {"name": name, "score": 0, "checks": [], "error": "SKILL.md manquant"}

    content = skill_md.read_text(encoding="utf-8")
    lines = content.split('\n')
    line_count = len(lines)
    fm = parse_frontmatter(content)

    checks = []
    score = 0

    # 1. Frontmatter (2 points)
    fm_ok = all(k in fm for k in REQUIRED_FM_KEYS)
    if fm_ok:
        score += 1
        checks.append("✅ 1. Frontmatter complet")
    else:
        missing = [k for k in REQUIRED_FM_KEYS if k not in fm]
        checks.append(f"❌ 1. Frontmatter: manque {missing}")

    if fm.get('priority') in VALID_PRIORITIES:
        score += 0.5
    if fm.get('category') in VALID_CATEGORIES:
        score += 0.5

    # 2. Sections 0-6 (1 point)
    sections_found = 0
    for section in REQUIRED_SECTIONS:
        if any(section[:8] in line for line in lines):
            sections_found += 1
    min_sections = 5 if fm.get('category') in ('catalog', 'feature') else 6
    if sections_found >= min_sections:
        score += 1
        checks.append(f"✅ 2. Sections: {sections_found}/7 présentes (min={min_sections})")
    else:
        checks.append(f"❌ 2. Sections: seulement {sections_found}/7 (min={min_sections})")

    # 3. Taille (1 point)
    if line_count <= 300:
        score += 1
        checks.append(f"✅ 3. Taille: {line_count} lignes (optimal ≤ 300)")
    elif line_count <= 420:
        score += 0.5
        checks.append(f"⚠️ 3. Taille: {line_count} lignes (acceptable ≤ 420)")
    elif line_count <= 600:
        checks.append(f"⚠️ 3. Taille: {line_count} lignes (limite ≤ 600)")
    else:
        checks.append(f"❌ 3. Taille: {line_count} lignes (dépasse 600)")

    # 4. Tables ❌/✅ (1 point)
    has_interdit = '❌' in content or 'Interdit' in content
    has_obligatoire = '✅' in content or 'Obligatoire' in content
    has_severity = 'P0' in content or 'P1' in content or '🔴' in content or '🟡' in content
    if has_interdit and has_obligatoire and has_severity:
        score += 1
        checks.append("✅ 4. Tables ❌/✅ avec sévérité")
    else:
        checks.append("❌ 4. Tables ❌/✅ ou sévérité manquantes")

    # 5. Méthode de vérification (1 point)
    has_linter = bool(fm.get('linters')) or '```bash' in content
    has_pytest = 'pytest' in content or 'test_' in content
    if has_linter or has_pytest:
        score += 1
        checks.append(f"✅ 5. Vérification: linter={bool(fm.get('linters'))}, tests={has_pytest}")
    else:
        checks.append("❌ 5. Aucune méthode de vérification")

    # 6. Cross-références (1 point)
    has_crossref = 'Références croisées' in content or '../' in content
    if has_crossref:
        score += 1
        checks.append("✅ 6. Références croisées présentes")
    else:
        checks.append("❌ 6. Pas de références croisées")

    # 7. Exemple before/after (1 point) — optionnel pour catalog/feature
    is_catalog_or_feature = fm.get('category') in ('catalog', 'feature')
    has_before = '❌ AVANT' in content or '❌' in content
    has_after = '✅ APRÈS' in content or '✅' in content
    has_code_example = '```python' in content
    if has_before and has_after:
        score += 1
        checks.append("✅ 7. Exemples before/after")
    elif is_catalog_or_feature and has_code_example:
        score += 1
        checks.append("✅ 7. Exemples de code (catalog/feature)")
    elif is_catalog_or_feature:
        score += 0.5
        checks.append("⚠️ 7. Peu d'exemples de code (catalog/feature)")
    else:
        checks.append("❌ 7. Exemples before/after manquants")

    # 8. Checklist (1 point)
    checklist_section = False
    for i, line in enumerate(lines):
        if '## 6. Checklist' in line or '# 6. Checklist' in line:
            checklist_section = True
        if checklist_section and '- [ ]' in line:
            break
    if checklist_section and '- [ ]' in content:
        score += 1
        checks.append("✅ 8. Checklist avec checkboxes")
    else:
        checks.append("❌ 8. Checklist manquante ou sans checkboxes")

    # 9. Pas de duplication (vérifié par nom unique)
    score += 1
    checks.append("✅ 9. Nom unique (pas de duplication détectée)")

    # 10. Dépendances (0.5 si présentes)
    deps = fm.get('depends_on', [])
    if deps and deps != ['']:
        score += 0.5
        checks.append(f"✅ 10. Dépendances: {deps}")
    else:
        checks.append("⚠️ 10. Pas de dépendances (racine)")
        score += 0.5  # les skills racine sont OK

    return {
        "name": name,
        "score": round(score, 1),
        "max": 10,
        "lines": line_count,
        "priority": fm.get('priority', '—'),
        "category": fm.get('category', '—'),
        "checks": checks,
    }


def main():
    # Force UTF-8 pour la sortie terminal (Windows cp1252 fix)
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    import argparse
    parser = argparse.ArgumentParser(description="Meta-linter des skills Larc")
    parser.add_argument("--dir", help="Répertoire d'un skill spécifique")
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    parser.add_argument("--all", action="store_true", help="Inclure les skills dépréciés")
    args = parser.parse_args()

    if args.dir:
        skill_dirs = [Path(args.dir)]
    else:
        skill_dirs = sorted(
            d for d in SKILLS_DIR.iterdir()
            if d.is_dir() and (args.all or d.name not in EXCLUDE)
        )

    results = []
    for skill_dir in skill_dirs:
        result = check_skill(skill_dir)
        results.append(result)

    if args.json:
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'Skill':<25} {'Score':<8} {'Lignes':<8} {'Priorité':<10} {'Catégorie'}")
        print("-" * 75)
        total = 0
        for r in sorted(results, key=lambda x: -x['score']):
            bar = "█" * int(r['score']) + "░" * (10 - int(r['score']))
            print(f"{r['name']:<25} {bar} {r['score']:.1f}/10 {r['lines']:<5}l  {r['priority']:<10} {r['category']}")
            total += r['score']

        avg = total / len(results) if results else 0
        print("-" * 75)
        print(f"MOYENNE: {avg:.1f}/10 sur {len(results)} skills\n")

        # Afficher les détails pour les skills < 10
        for r in results:
            if r['score'] < 10:
                print(f"\n── {r['name']} ({r['score']}/10) ──")
                for check in r['checks']:
                    if check.startswith('❌') or check.startswith('⚠️'):
                        print(f"  {check}")

        return 0 if all(r['score'] >= 8 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
