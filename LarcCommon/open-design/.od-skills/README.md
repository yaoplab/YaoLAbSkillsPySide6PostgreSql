# Larc — Base de Connaissances Agent

## Ordre de lecture pour un sub-agent

1. `CONTEXT.md` — Contexte du projet
2. `AGENTS.md` — Conventions générales
3. `skills/INDEX.md` — Index des skills
4. `skills/<nom>/SKILL.md` — Skill correspondant au module analysé

## Skills disponibles

| Skill | Priorité | Catégorie | Linter(s) |
|---|---|---|---|
| [auth-intranet](skills/auth-intranet/SKILL.md) | P0 | infrastructure | lint_auth_checker.py |
| [auth-oauth2](skills/auth-oauth2/SKILL.md) | P0 | infrastructure | lint_auth_checker.py |
| [auth-pin](skills/auth-pin/SKILL.md) | P1 | infrastructure | lint_auth_checker.py |
| [card-dashboard](skills/card-dashboard/SKILL.md) | P1 | design | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [card-grid-pattern](skills/card-grid-pattern/SKILL.md) | P0 | page-pattern | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [color-rules](skills/color-rules/SKILL.md) | P0 | design | lint_d1_color_checker.py |
| [dashboard-pattern](skills/dashboard-pattern/SKILL.md) | P0 | page-pattern | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [database-operations](skills/database-operations/SKILL.md) | P0 | infrastructure | lint_db_checker.py |
| [design-tokens](skills/design-tokens/SKILL.md) | P0 | design | lint_qss_hardcoding.py |
| [ergonomics](skills/ergonomics/SKILL.md) | P0 | design | lint_qss_hardcoding.py |
| [event-generator](skills/event-generator/SKILL.md) | P1 | feature | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [form-pattern](skills/form-pattern/SKILL.md) | P0 | page-pattern | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [graphify](skills/graphify/SKILL.md) | P0 | infra | — |
| [larc-testing](skills/larc-testing/SKILL.md) | P1 | quality | lint_test_coverage.py |
| [pyside6-wrapper](skills/pyside6-wrapper/SKILL.md) | P0 | infrastructure | lint_safe_slot.py, lint_file_size.py |
| [search-detail-pattern](skills/search-detail-pattern/SKILL.md) | P0 | page-pattern | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [sidebar-spec](skills/sidebar-spec/SKILL.md) | P1 | design | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [student-record](skills/student-record/SKILL.md) | P0 | feature | lint_d1_color_checker.py, lint_qss_hardcoding.py |
| [sync](skills/sync/SKILL.md) | P1 | infrastructure | lint_db_checker.py |
| [theme-reactivity](skills/theme-reactivity/SKILL.md) | P1 | design | audit_theme_reactive.py |
| [toolkit-reference](skills/toolkit-reference/SKILL.md) | P1 | catalog | lint_qss_hardcoding.py |
| [zero-hardcoding](skills/zero-hardcoding/SKILL.md) | P0 | design | lint_qss_hardcoding.py |

## Agents reviewers

| Agent | Skills couverts |
|---|---|
| [auth-reviewer](agents/auth-reviewer.md) | Voir le fichier agent |
| [design-reviewer](agents/design-reviewer.md) | Voir le fichier agent |
| [feature-reviewer](agents/feature-reviewer.md) | Voir le fichier agent |
| [graphify-reviewer](agents/graphify-reviewer.md) | Voir le fichier agent |
| [infra-reviewer](agents/infra-reviewer.md) | Voir le fichier agent |
| [pyside6-reviewer](agents/pyside6-reviewer.md) | Voir le fichier agent |
| [testing-reviewer](agents/testing-reviewer.md) | Voir le fichier agent |

## Structure

| Dossier | Contenu |
|---|---|
| `skills/` | Skills (1 par fonctionnalité) |
| `agents/` | Agents reviewers |

## Règle absolue

**Lire ce dossier AVANT d'analyser. Ne jamais modifier les fichiers du projet.**