# Larc Skills — Index

Base de connaissances agent pour le projet Larc. **Lis ce fichier en premier.**

## Ordre de lecture recommande

| # | Skill | Priorite | Pourquoi le lire |
|---|---|---|---|
| 1 | [`design-tokens`](design-tokens/SKILL.md) | P0 | Tous les tokens numeriques — prerequis a tout le reste |
| 2 | [`color-rules`](color-rules/SKILL.md) | P0 | Palette et regles de couleur — la source de 80% des bugs visuels |
| 3 | [`zero-hardcoding`](zero-hardcoding/SKILL.md) | P0 | Regle absolue — toute valeur px doit etre un token |
| 4 | [`theme-reactivity`](theme-reactivity/SKILL.md) | P1 | Pattern _STYLE + _restyle_all — comment reagir au changement de theme |
| 5 | [`pyside6-wrapper`](pyside6-wrapper/SKILL.md) | P0 | @safe_slot obligatoire, anti-patterns Qt, regle 1000 lignes |
| 6 | [`sidebar-spec`](sidebar-spec/SKILL.md) | P1 | Specification visuelle exacte du sidebar (25 regles) |
| 7 | [`ergonomics`](ergonomics/SKILL.md) | P1 | Ergonomie des fenetres de liste (recherche, tableaux, etats vides) |
| 8 | [`testing`](testing/SKILL.md) | P1 | Strategie de test 2 phases (mock + reel) |
| 9 | [`auth-oauth2`](auth-oauth2/SKILL.md) | P0 | Auth Google OAuth2 PKCE pour superviseurs |
| 10 | [`auth-intranet`](auth-intranet/SKILL.md) | P0 | Auth PostgreSQL local pour tous les utilisateurs |
| 11 | [`auth-pin`](auth-pin/SKILL.md) | P1 | Auth par code PIN hors connexion pour professeurs |
| 12 | [`database-operations`](database-operations/SKILL.md) | P0 | Singleton DB, connexions, cycle de vie |
| 13 | [`sync`](sync/SKILL.md) | P1 | Synchronisation PostgreSQL local↔Supabase cloud |
| 14 | [`toolkit-reference`](toolkit-reference/SKILL.md) | P1 | Catalogue widgets + architecture phibuilder |
| 15 | [`event-generator`](event-generator/SKILL.md) | P1 | Wizard d'evenements eleves (absences, retards) |
| 16 | [`card-dashboard`](card-dashboard/SKILL.md) | P1 | Vignettes configurables par role (secretaire/superviseur/prof) |
| 17 | [`student-record`](student-record/SKILL.md) | P0 | Dossier eleve par categories + documents (secretaire/RH) |
| 18 | [`dashboard-pattern`](dashboard-pattern/SKILL.md) | P0 | 🆕 Pattern canonique de page tableau de bord |
| 19 | [`search-detail-pattern`](search-detail-pattern/SKILL.md) | P0 | 🆕 Pattern canonique de recherche + fiche detail |
| 20 | [`form-pattern`](form-pattern/SKILL.md) | P0 | 🆕 Pattern canonique de formulaire par sections |
| 21 | [`card-grid-pattern`](card-grid-pattern/SKILL.md) | P0 | 🆕 Pattern canonique de grille de vignettes responsive |
| 22 | [`graphify`](graphify/SKILL.md) | P0 | Graphe de connaissances du codebase — "cerveau Obsidian" interrogeable |
| 23 | [`scolarite-finance`](scolarite-finance/SKILL.md) | P0 | 🆕 Règles métier scolarité : balance, statut, projection, alertes |

## Arbre de dependances

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

Page patterns (utilisent les 6 skills design) :
    dashboard-pattern
    search-detail-pattern
    form-pattern
    card-grid-pattern

Metier (utilise les skills design + page patterns) :
    scolarite-finance
```

Les skills de gauche (design-tokens, pyside6-wrapper) sont les fondations.
Les skills de droite sont specialises et supposent la lecture prealable des fondations.
Les **page patterns** sont des compositions des 6 skills design : ils ne definissent pas
de nouvelles regles, ils documentent la structure spatiale canonique de chaque type de page.

## Skills et leurs linters

| Skill | Linter(s) | Script |
|---|---|---|
| `scolarite-finance` | D-linter + R-linter (herite de design-tokens+color-rules) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| `graphify` | — (verification manuelle : `graphify .`) | — |
| `design-tokens` | R-linter (R1-R11, R14, R17) | `scripts/lint_qss_hardcoding.py` |
| `color-rules` | D-linter (D1, D3-D7, J7) | `scripts/lint_d1_color_checker.py` |
| `theme-reactivity` | Audit theme reactive | `scripts/audit_theme_reactive.py` |
| `zero-hardcoding` | R-linter (R1-R13, R15-R16) | `scripts/lint_qss_hardcoding.py` |
| `sidebar-spec` | D-linter + R-linter (couvrent deja K) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| `ergonomics` | R-linter (Q1+Q3, Q2) | `scripts/lint_qss_hardcoding.py` |
| `dashboard-pattern` | D-linter + R-linter (herite de design-tokens+color-rules) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| `search-detail-pattern` | D-linter + R-linter (herite) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| `form-pattern` | D-linter + R-linter (herite) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| `card-grid-pattern` | D-linter + R-linter (herite) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| `testing` | Coverage checker | `scripts/lint_test_coverage.py` |
| `auth-oauth2` | — (verification manuelle : config.ini + Google Console) | — |
| `auth-intranet` | — (verification manuelle : PostgreSQL + SHA-256) | — |
| `auth-pin` | — (verification manuelle : SQLite + SHA-256) | — |
| `database-operations` | — (verification manuelle : connexion + config) | — |
| `sync` | — (verification manuelle : sync_table + logs) | — |
| `toolkit-reference` | R-linter (R17) | `lint_qss_hardcoding.py --dir .\LarcCommon` |
| `event-generator` | D-linter + R-linter (couvrent les hex hardcodes) | `lint_d1_color_checker.py` |
| `pyside6-wrapper` | Safe slot + File size | `scripts/lint_safe_slot.py` + `scripts/lint_file_size.py` |

## Agent Reviewers

| Reviewer | Skills couverts | Fichier |
|---|---|---|
| `design-reviewer` | design-tokens, color-rules, theme-reactivity, zero-hardcoding, sidebar-spec, ergonomics, card-dashboard, student-record, dashboard-pattern, search-detail-pattern, form-pattern, card-grid-pattern | [agents/design-reviewer.md](../agents/design-reviewer.md) |
| `pyside6-reviewer` | pyside6-wrapper | [agents/pyside6-reviewer.md](../agents/pyside6-reviewer.md) |
| `testing-reviewer` | testing | [agents/testing-reviewer.md](../agents/testing-reviewer.md) |
| `auth-reviewer` | auth-oauth2, auth-intranet, auth-pin | [agents/auth-reviewer.md](../agents/auth-reviewer.md) |
| `infra-reviewer` | graphify, database-operations, sync | [agents/infra-reviewer.md](../agents/infra-reviewer.md) |
| `graphify-reviewer` | graphify | [agents/graphify-reviewer.md](../agents/graphify-reviewer.md) |
| `feature-reviewer` | scolarite-finance, event-generator, card-dashboard, student-record, toolkit-reference, dashboard-pattern, search-detail-pattern, form-pattern, card-grid-pattern | [agents/feature-reviewer.md](../agents/feature-reviewer.md) |

## Regle absolue

**Lire le skill correspondant AVANT de modifier un fichier du module concerne.**
**Si un linter existe, l'executer APRES chaque modification.**
