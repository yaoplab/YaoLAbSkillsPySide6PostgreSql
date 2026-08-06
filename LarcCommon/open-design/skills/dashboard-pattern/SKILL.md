---
skill: dashboard-pattern
version: "1.0"
priority: P0
category: page-pattern
depends_on: [design-tokens, color-rules, zero-hardcoding, theme-reactivity, ergonomics]
applies_to: [LarcSecretaire, LarcSuperviseur, LarcProf, LarcHub]
linters: [lint_d1_color_checker.py, lint_qss_hardcoding.py]
reviewers: [design-reviewer, feature-reviewer]
subsystems: [DP]
---

# Skill: Dashboard Pattern — Page Tableau de Bord

## 0. Contexte

**Projet** : Tous les modules Larc (Secretaire, Superviseur, Prof, Hub)
**Fichier de reference** : `LarcSecretaire/views/main_window.py::_build_dashboard()` — implementation de reference
**Utilisateurs** : Developpeurs de vues dashboard ET agents IA construisant des tableaux de bord

Ce skill definit le **pattern canonique de page dashboard** pour toutes les applis Larc. Une page dashboard
doit etre structurellement identique d'une appli a l'autre, quel que soit le contenu metier.

## 1. Fonction Principale

### Type : Systeme Ferme

**Entree** : Une page blanche sans structure
**Sortie** : Un dashboard M3 avec KPI cards, tables, graphiques, et alertes
**Traitement** : Appliquer le patron DP1-DP8 dans l'ordre

## 2. Contraintes Fondamentales

### Architecture spatiale obligatoire

```
┌──────────────────────────────────────────────────────────────────────┐
│ DP1 — SCOPE LABEL                                                    │
│ headline_small, centre, gras, couleur programme                      │
├──────────────────────────────────────────────────────────────────────┤
│ DP2 — KPI ROW 1 (4 cards horizontales)                               │
│ total │ college │ lycee │ enseignants                                │
│ valeur large + label small en dessous                                │
│ M3Frame#kpi_card, FixedHeight = ds.kpi_card_height                  │
├──────────────────────────────────────────────────────────────────────┤
│ DP3 — KPI ROW 2 (4 cards actionnables)                               │
│ Sans photo │ Sans parent │ Sans email │ Doss. incomplets             │
│ Icone + valeur sur meme ligne, label small en dessous                │
│ M3Frame#kpi_small, FixedHeight = ds.kpi_card_height                 │
│ Cursor PointingHand + mousePressEvent = action                      │
├──────────────────────────────────────────────────────────────────────┤
│ DP4 — BODY (colonne gauche 1 + colonne droite 2)                     │
│                                                                      │
│  ┌─────────────────────────┐  ┌────────────────────────────────┐    │
│  │ DP4a — TABLEAU STATS   │  │ DP4b — GRAPHIQUE QChartView     │    │
│  │ M3TableWidget           │  │ Barres empilees par programme   │    │
│  │ Pgm │ Actifs │ Taux │..│  │ Hauteur = ds.golden_height(610) │    │
│  │ Stretch sur 6 colonnes  │  │ Antialiasing ON                 │    │
│  │ MaxHeight = HUGE*2      │  │                                 │    │
│  │ Scroll horizontal OFF   │  │                                 │    │
│  └─────────────────────────┘  └────────────────────────────────┘    │
│  ┌─────────────────────────┐                                        │
│  │ DP4c — TABLEAU ENSEIGNANTS│                                      │
│  │ Matiere │ Enseignants    │                                        │
│  │ MaxHeight = COLOSSAL     │                                        │
│  └─────────────────────────┘                                        │
├──────────────────────────────────────────────────────────────────────┤
│ DP5 — RATIO GENRE                                                    │
│ Centre, bold, padding ds.space_xxs                                  │
├──────────────────────────────────────────────────────────────────────┤
│ DP6 — ALERTES                                                        │
│ M3Label, wordWrap, panel background                                 │
└──────────────────────────────────────────────────────────────────────┘
```

### Table des regles DP

| # | Regle | Interdit | Obligatoire | Priorite |
|---|---|---|---|---|
| DP1 | **Scope label** en haut | Titre en `title_large` | `headline_small`, centre, couleur programme | P0 |
| DP2 | **KPI row 1** — 4 cards chiffrees | `QFrame` sans objectName | `M3Frame#kpi_card`, `FixedHeight = ds.kpi_card_height`, valeur en `headline_small`, label en `label_small` | P0 |
| DP3 | **KPI row 2** — 4 cards actionnables | Pas de curseur, pas de clic | `M3Frame#kpi_small`, icone 16px + valeur cote a cote, `cursor PointingHand`, `mousePressEvent` | P0 |
| DP4 | **Body** — ratio 1:2 gauche/droite | Layout desequilibre | `QHBoxLayout` avec stretch 1 et 2 | P0 |
| DP4a | **Tableau stats** — 6 colonnes | Colonnes a largeur fixe | `M3HeaderView.Stretch` sur chaque colonne, `MaxHeight = HUGE*2`, `setHorizontalScrollBarPolicy(AlwaysOff)` | P0 |
| DP4b | **Graphique** QChartView | Sans antialiasing | `setRenderHint(Antialiasing)`, `setMinimumHeight(golden_height(610))` | P1 |
| DP4c | **Tableau enseignants** | Stretch ou defilement horizontal | 2 colonnes en Stretch, `MaxHeight = COLOSSAL` | P1 |
| DP5 | **Ratio genre** | Absent | Centre, bold, padding ds.space_xxs | P1 |
| DP6 | **Alertes** | Absentes ou en popup modal | M3Label inline, wordWrap=True, fond panel | P1 |
| DP7 | **Toutes les KPI cards** doivent etre restylees | `_restyle()` ne touche pas les KPI | `_update_dashboard_style()` ou `_restyle()` complet couvre tous les objectNames KPI | P0 |
| DP8 | **Conteneur** = `M3ScrollArea` | `QWidget` simple non scrollable | `setWidgetResizable(True)`, `inner = QWidget()` comme contenu | P0 |

## 3. Code canonique

```python
def _build_dashboard(self) -> QWidget:
    page = M3ScrollArea()
    page.setWidgetResizable(True)
    # DP8 : scroll area comme conteneur
    page.setObjectName("dashboard_page")

    inner = QWidget()
    # R16 : viewport transparent
    page.viewport().setStyleSheet("background: transparent;")
    inner.setAttribute(Qt.WA_StyledBackground, True)
    inner.setStyleSheet("background: transparent;")

    layout = QVBoxLayout(inner)
    layout.setContentsMargins(ds.space_sm, ds.space_sm, ds.space_sm, ds.space_sm)
    layout.setSpacing(ds.space_sm)

    # DP1 — Scope label
    self._scope_label = M3Label(style="headline_small")
    self._scope_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(self._scope_label)

    # DP2 — KPI row 1
    kpi_row = QHBoxLayout()
    kpi_row.setSpacing(ds.space_xs)
    self._kpi_widgets = {}
    for key, label in KPI_ITEMS:
        f = M3Frame()
        f.setObjectName("kpi_card")
        f.setFixedHeight(ds.kpi_card_height)
        fl = QVBoxLayout(f)
        fl.setAlignment(Qt.AlignCenter)
        v = M3Label("—")
        v.setObjectName("kpi_value")
        v.setAlignment(Qt.AlignCenter)
        l = M3Label(label)
        l.setObjectName("kpi_label")
        l.setAlignment(Qt.AlignCenter)
        fl.addWidget(v)
        fl.addWidget(l)
        self._kpi_widgets[key] = v
        kpi_row.addWidget(f, 1)
    layout.addLayout(kpi_row)

    # DP3 — KPI row 2 (actionnable)
    kpi_row2 = QHBoxLayout()
    kpi_row2.setSpacing(ds.space_xs)
    for key, label, icon_name, color_role in ACTION_KPIS:
        f = M3Frame()
        f.setObjectName("kpi_small")
        f.setFixedHeight(ds.kpi_card_height)
        f.setCursor(Qt.PointingHandCursor)
        fl = QVBoxLayout(f)
        fl.setAlignment(Qt.AlignCenter)
        fl.setSpacing(ds.space_xxs)
        icon_row = QHBoxLayout()
        icon_row.setAlignment(Qt.AlignCenter)
        icon_row.setSpacing(ds.space_xxs)
        ico = QLabel()
        ico.setPixmap(md3_icon(icon_name, color=getattr(ds.p, color_role), size=16).pixmap(16, 16))
        icon_row.addWidget(ico)
        v = M3Label("—")
        v.setObjectName("kpi_small_value")
        v.setAlignment(Qt.AlignCenter)
        icon_row.addWidget(v)
        fl.addLayout(icon_row)
        l = M3Label(label)
        l.setObjectName("kpi_small_label")
        l.setAlignment(Qt.AlignCenter)
        fl.addWidget(l)
        f.mousePressEvent = lambda ev, k=key: self._on_action_kpi(k)
        kpi_row2.addWidget(f, 1)
    layout.addLayout(kpi_row2)

    # DP4 — Body (gauche 1, droite 2)
    body_row = QHBoxLayout()
    body_row.setSpacing(ds.space_sm)

    left_col = QVBoxLayout()
    left_col.setSpacing(ds.space_xs)

    # DP4a — Tableau stats (6 colonnes Stretch)
    self._dashboard_table = M3TableWidget()
    self._dashboard_table.setColumnCount(6)
    self._dashboard_table.setHorizontalHeaderLabels([...])
    hdr = self._dashboard_table.horizontalHeader()
    for i in range(6):
        hdr.setSectionResizeMode(i, M3HeaderView.Stretch)
    self._dashboard_table.setMaximumHeight(ds.sp(SpacingToken.HUGE) * 2)
    self._dashboard_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    self._dashboard_table.verticalHeader().setDefaultSectionSize(ds.table_row_min)
    self._dashboard_table.setStyleSheet(ds.table_qss())
    left_col.addWidget(self._dashboard_table)

    # DP4c — Tableau enseignants (2 colonnes Stretch)
    self._teacher_table = M3TableWidget()
    # ... 2 colonnes en Stretch, MaxHeight = COLOSSAL

    body_row.addLayout(left_col, 1)

    # DP4b — Graphique
    right_col = QVBoxLayout()
    right_col.setSpacing(ds.space_xs)
    self._chart_view = QChartView()
    self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
    self._chart_view.setMinimumHeight(ds.golden_height(610))
    right_col.addWidget(self._chart_view, 1)
    body_row.addLayout(right_col, 2)

    layout.addLayout(body_row)

    # DP5 — Ratio genre
    self._gender_ratio_label = M3Label()
    self._gender_ratio_label.setStyleSheet(f"font-weight: bold; padding: {ds.space_xxs}px;")
    layout.addWidget(self._gender_ratio_label, 0, Qt.AlignCenter)

    # DP6 — Alertes
    self._alert_label = M3Label()
    self._alert_label.setStyleSheet(f"color: {ds.p.text_strong}; padding: {ds.space_xs}px;")
    self._alert_label.setWordWrap(True)
    layout.addWidget(self._alert_label)

    layout.addStretch()
    page.setWidget(inner)
    return page
```

### Pattern _STYLE pour le dashboard

```python
@property
def _DASHBOARD_STYLE(self) -> str:
    p = ds.p
    return f"""
        QWidget#dashboard_page {{ background: {p.background}; }}
        M3Frame#kpi_card {{
            background: {p.surface}; color: {p.text_strong};
            border: 1px solid {p.outline_variant};
            border-radius: {ds.radius_md}px;
        }}
        M3Label#kpi_value {{
            font-size: {theme_manager.font_size(28)}px;
            font-weight: bold;
            color: {p.primary};
        }}
        M3Label#kpi_label {{
            font-size: {theme_manager.font_size(11)}px;
            color: {p.text_soft};
        }}
        M3Frame#kpi_small {{
            background: {p.surface}; color: {p.text_strong};
            border: 1px solid {p.outline_variant};
            border-radius: {ds.radius_md}px;
        }}
        M3Frame#kpi_small:hover {{
            background: {p.surface_variant};
        }}
        M3Label#kpi_small_value {{
            font-size: {theme_manager.font_size(22)}px;
            font-weight: bold;
            color: {p.primary};
        }}
    """
```

## 5. Step by Step

1. Creer le conteneur `M3ScrollArea` (DP8)
2. Ajouter le scope label (DP1)
3. Construire la rangee 1 de KPI (DP2) — 4 cards chiffrees
4. Construire la rangee 2 de KPI actionnables (DP3) — icone + valeur
5. Construire le body en 2 colonnes (DP4) — ratio 1:2
6. Remplir la colonne gauche : tableaux stats (DP4a) + enseignants (DP4c)
7. Remplir la colonne droite : graphique QChartView (DP4b)
8. Ajouter le ratio genre (DP5)
9. Ajouter les alertes (DP6)
10. Connecter `theme_changed` → `_restyle` qui re-applique `_DASHBOARD_STYLE` (DP7)

## 6. Checklist

- [ ] DP1 : scope label en headline_small, centre
- [ ] DP2 : 4 KPI cards (kpi_card), FixedHeight ds.kpi_card_height
- [ ] DP3 : 4 KPI actionnables (kpi_small), icone 16px, cursor PointingHand, mousePressEvent
- [ ] DP4 : body ratio 1:2, tableaux en Stretch, graphique antialiased
- [ ] DP4a : tableau stats 6 colonnes Stretch, MaxHeight HUGE*2, scroll horizontal off
- [ ] DP4c : tableau enseignants 2 colonnes Stretch, MaxHeight COLOSSAL
- [ ] DP5 : ratio genre centre, bold, padding
- [ ] DP6 : alertes inline, wordWrap
- [ ] DP7 : _DASHBOARD_STYLE property + _restyle couvre tous les objectNames KPI
- [ ] DP8 : conteneur M3ScrollArea, viewport transparent
- [ ] 0 hex hardcode — tout via ds.p.*
- [ ] 0 pixel litteral — tout via tokens
- [ ] theme_changed → _restyle() reconnecte le QSS
- [ ] Tous les M3Frame ont setAttribute(Qt.WA_StyledBackground, True) ou sont des M3Frame

## References croisees

- **[design-tokens](../design-tokens/SKILL.md)** — ds.kpi_card_height, SpacingToken.HUGE/COLOSSAL
- **[color-rules](../color-rules/SKILL.md)** — D1 (color: explicite sur tous les labels)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — DP7 pattern _STYLE + _restyle
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — R10 (pas de setAlternatingRowColors)
- **[ergonomics](../ergonomics/SKILL.md)** — Q1 (hover sur les lignes des tableaux)
