# Larc Skills — Index

Base de connaissances agent pour le projet Larc. **Lis ce fichier en premier.**

## Ordre de lecture recommandé

| # | Skill | Priorité | Pourquoi le lire |
|---|---|---|---|
| 1 | [`design-tokens`](design-tokens/SKILL.md) | P0 | Tous les tokens numériques — prérequis à tout le reste |
| 2 | [`color-rules`](color-rules/SKILL.md) | P0 | Palette et règles de couleur — la source de 80% des bugs visuels |
| 3 | [`zero-hardcoding`](zero-hardcoding/SKILL.md) | P0 | Règle absolue — toute valeur px doit être un token |
| 4 | [`theme-reactivity`](theme-reactivity/SKILL.md) | P1 | Pattern _STYLE + _restyle_all — comment réagir au changement de thème |
| 5 | [`pyside6-wrapper`](pyside6-wrapper/SKILL.md) | P0 | @safe_slot obligatoire, anti-patterns Qt, règle 1000 lignes |
| 6 | [`sidebar-spec`](sidebar-spec/SKILL.md) | P1 | Spécification visuelle exacte du sidebar (25 règles) |
| 7 | [`ergonomics`](ergonomics/SKILL.md) | P1 | Ergonomie des fenêtres de liste (recherche, tableaux, états vides) |
| 8 | [`testing`](testing/SKILL.md) | P1 | Stratégie de test 2 phases (mock + réel) |
| 9 | [`auth-oauth2`](auth-oauth2/SKILL.md) | P0 | Auth Google OAuth2 PKCE pour superviseurs |
| 10 | [`auth-intranet`](auth-intranet/SKILL.md) | P0 | Auth PostgreSQL local pour tous les utilisateurs |
| 11 | [`auth-pin`](auth-pin/SKILL.md) | P1 | Auth par code PIN hors connexion pour professeurs |
| 12 | [`database-operations`](database-operations/SKILL.md) | P0 | Singleton DB, connexions, cycle de vie |
| 13 | [`sync`](sync/SKILL.md) | P1 | Synchronisation PostgreSQL local↔Supabase cloud |
| 14 | [`toolkit-reference`](toolkit-reference/SKILL.md) | P1 | Catalogue widgets + architecture phibuilder |
| 15 | [`event-generator`](event-generator/SKILL.md) | P1 | Wizard d'événements élèves (absences, retards) |
| 16 | [`card-dashboard`](card-dashboard/SKILL.md) | P1 | Vignettes configurables par rôle (secrétaire/superviseur/prof) |
| 17 | [`student-record`](student-record/SKILL.md) | P0 | 🆕 Dossier élève par catégories + documents (secrétaire/RH) |

## Arbre de dépendances

```
design-tokens ─────────────────────────────────────────┐
    │                                                   │
    ├── color-rules ──┬── theme-reactivity              │
    │                 │       │                          │
    │                 │       └── sidebar-spec           │
    │                 │                                  │
    │                 └── zero-hardcoding ───────────────┤
    │                                                   │
    └── ergonomics ─────────────────────────────────────┤
                                                        │
auth-oauth2 ────────────────────────────────────────────┤
    │                                                   │
auth-intranet ──────────────────────────────────────────┤
    │                                                   │
    └── auth-pin ───────────────────────────────────────┘
pyside6-wrapper ────────────────────────────────────────┤
    │                                                   │
    └── testing ────────────────────────────────────────┘
```

Les skills de gauche (design-tokens, pyside6-wrapper) sont les fondations.
Les skills de droite sont spécialisés et supposent la lecture préalable des fondations.

## Skills et leurs linters

| Skill | Linter(s) | Script |
|---|---|---|
| `design-tokens` | R-linter (R1-R11, R14, R17) | `scripts/lint_qss_hardcoding.py` |
| `color-rules` | D-linter (D1, D3-D7, J7) | `scripts/lint_d1_color_checker.py` |
| `theme-reactivity` | Audit theme reactive | `scripts/audit_theme_reactive.py` |
| `zero-hardcoding` | R-linter (R1-R13, R15-R16) | `scripts/lint_qss_hardcoding.py` |
| `sidebar-spec` | D-linter + R-linter (couvrent déjà K) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| `ergonomics` | R-linter (Q1+Q3, Q2) | `scripts/lint_qss_hardcoding.py` |
| `testing` | Coverage checker | `scripts/lint_test_coverage.py` |
| `auth-oauth2` | — (vérification manuelle : config.ini + Google Console) | — |
| `auth-intranet` | — (vérification manuelle : PostgreSQL + SHA-256) | — |
| `auth-pin` | — (vérification manuelle : SQLite + SHA-256) | — |
| `database-operations` | — (vérification manuelle : connexion + config) | — |
| `sync` | — (vérification manuelle : sync_table + logs) | — |
| `toolkit-reference` | R-linter (R17) | `lint_qss_hardcoding.py --dir .\LarcCommon` |
| `event-generator` | D-linter + R-linter (couvrent les hex hardcodés) | `lint_d1_color_checker.py` |
| `pyside6-wrapper` | Safe slot + File size | `scripts/lint_safe_slot.py` (nouveau) + `scripts/lint_file_size.py` (nouveau) |

## Agent Reviewers

| Reviewer | Skills couverts | Fichier |
|---|---|---|
| `design-reviewer` | design-tokens, color-rules, theme-reactivity, zero-hardcoding, sidebar-spec, ergonomics, card-dashboard, student-record | [agents/design-reviewer.md](../agents/design-reviewer.md) |
| `pyside6-reviewer` | pyside6-wrapper | [agents/pyside6-reviewer.md](../agents/pyside6-reviewer.md) |
| `testing-reviewer` | testing | [agents/testing-reviewer.md](../agents/testing-reviewer.md) |
| `auth-reviewer` 🆕 | auth-oauth2, auth-intranet, auth-pin | [agents/auth-reviewer.md](../agents/auth-reviewer.md) |
| `infra-reviewer` 🆕 | database-operations, sync | [agents/infra-reviewer.md](../agents/infra-reviewer.md) |
| `feature-reviewer` 🆕 | event-generator, card-dashboard, student-record, toolkit-reference | [agents/feature-reviewer.md](../agents/feature-reviewer.md) |

## Règle absolue

**Lire le skill correspondant AVANT de modifier un fichier du module concerné.**
**Si un linter existe, l'exécuter APRÈS chaque modification.**
