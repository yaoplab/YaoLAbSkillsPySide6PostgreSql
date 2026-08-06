---
skill: pyside6-wrapper
version: "1.0"
priority: P0
category: infrastructure
depends_on: [theme-reactivity]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcDesign]
linters: [lint_safe_slot.py, lint_file_size.py]
reviewers: [pyside6-reviewer]
subsystems: [A, B, C, D, E, F, J]
---

# Skill: PySide6 Wrapper

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof, Design, Hub)
**Module** : `LarcCommon/larccommon/safe_slot.py`
**Utilisateurs** : Tous les développeurs Larc
**Dépendances** : `PySide6>=6.5`, `LarcCommon/larccommon/logger.py`

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Slot Qt non protégé (`button.clicked`, `table.itemChanged`, etc.)
**Sortie** : Slot protégé contre les crashes silencieux avec logging + message debug
**Traitement** : Appliquer `@safe_slot(label)` sur tous les slots Qt

## 2. Contraintes Fondamentales

| # | Contrainte | Gravité |
|---|---|---|
| C1 | **Tout slot Qt est décoré** `@safe_slot("App.section.action")` | 🔴 P0 |
| C2 | **Aucun `lambda:` nu** dans `connect()` — slot nommé ou `functools.partial` | 🔴 P0 |
| C3 | `set_debug(True)` en dev, `set_debug(False)` en prod | 🟡 P1 |
| C4 | **Aucun fichier > 1000 lignes** — extraire dans sous-modules | 🔴 P0 |
| C5 | Aucun `except Exception: pass` muet — logger ou `@safe_slot` | 🟡 P1 |
| C6 | Pas de `print()` dans les handlers — utiliser `log()` | 🟡 P1 |
| C7 | `QWidget()`/`QDialog()` ciblé par QSS → `ThemedWidget()`/`ThemedDialog()` | 🔴 P0 |

### Sous-système A — Anti-patterns Qt

| # | ❌ Interdit | ✅ Obligatoire |
|---|---|---|
| A1 | `button.clicked.connect(lambda: self.save())` | `button.clicked.connect(self._on_save)` + `@safe_slot("save")` |
| A2 | `table.itemChanged.connect(lambda i: self.on_change(i))` | `table.itemChanged.connect(self._on_item_change)` + `@safe_slot("table.change")` |
| A3 | `try: ... except: pass` muet | `@safe_slot` gère l'exception automatiquement |
| A4 | `QMessageBox.critical` sans logger | `@safe_slot` logge AVANT la boîte de dialogue |
| A5 | `print()` dans les handlers | `from larccommon.logger import log` via `@safe_slot` |
| A6 | `setContentsMargins(6,6,6,6)` en dur | `ds.space_*` (voir **[design-tokens](../design-tokens/SKILL.md)**) |
| A7 | `setFixedWidth(233)` en dur | Token `ds.sidebar_width` (voir **[design-tokens](../design-tokens/SKILL.md)**) |

### Sous-système B — Dialogues M3

| # | Contrainte |
|---|---|
| B1 | Tout dialogue modal utilise `M3Dialog` avec `setModal(True)` |
| B2 | Fermeture : `dialog.accept()` ou `dialog.reject()` |
| B3 | Avant nouveau dialogue : fermer le précédent |
| B4 | Dialogues en lazy init (pas dans le constructeur) |

### Sous-système C — FilePicker

| # | Contrainte |
|---|---|
| C1 | `QFileDialog.getOpenFileName()` — version statique |
| C2 | Pas de `exec()` bloquant |
| C3 | Filtre : `"Images (*.png *.jpg *.webp);;Tous (*)"` |

### Sous-système D — Safe Update

| # | Contrainte |
|---|---|
| D1 | `widget.update()` sur widget non monté → `try: except RuntimeError: pass` |
| D2 | Signaux cross-thread : `Signal` + `@Slot()` avec paramètre `QThread` |

### Sous-système E — Safe Slot (décorateur)

| # | Contrainte |
|---|---|
| E1 | Tout handler est décoré : `@safe_slot("App.section.action")` |
| E2 | Label unique obligatoire : `"MainWindow.btn_save_student"` |
| E3 | En cas d'erreur : log automatique + QMessageBox.critical si debug |
| E4 | `set_debug(True)` active logs START/OK/ERROR avec temps d'exécution |
| E5 | `set_debug(False)` désactive les logs (prod) |
| E6 | **Label interdit** : `_` comme nom de variable (écrase la fonction i18n) — utiliser `_outer`, `_ignored` |

### Sous-système F — Règle des 1000 lignes

| # | Contrainte |
|---|---|
| F1 | Aucun fichier > 1000 lignes |
| F2 | Si > 500 lignes : envisager fractionnement par domaine |
| F3 | Un fichier = une responsabilité (un écran, un module) |
| F4 | Exception : fichiers générés automatiquement (SQL, migrations) |

### Sous-système J — Exemples complexes

**Slot avec arguments :**

```python
@safe_slot("StudentTable.on_cell_changed")
def _on_cell_changed(self, row: int, col: int):
    item = self._table.item(row, col)
    if item is None:
        return
    value = item.text().strip()
    self._update_field(row, col, value)
```

**Slot dans un QThread (cross-thread safe) :**

```python
class DataWorker(QThread):
    data_ready = Signal(list)
    error_occurred = Signal(str)
    finished = Signal()
    
    def run(self):
        try:
            result = self._heavy_computation()
            self.data_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

# Dans la vue
@safe_slot("MaVue.on_data_ready")
def _on_data_ready(self, data: list):
    self._populate_table(data)
```

## 3. Code complet

### safe_slot (LarcCommon/larccommon/safe_slot.py)

```python
import functools, time, traceback
from PySide6.QtWidgets import QMessageBox
from larccommon.logger import log as logger

DEBUG = False

def set_debug(enabled: bool):
    global DEBUG
    DEBUG = enabled

def safe_slot(label: str = ""):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.time()
            if DEBUG:
                logger(f"[SLOT] {label} | START")
            try:
                result = func(*args, **kwargs)
                if DEBUG:
                    elapsed = (time.time() - t0) * 1000
                    logger(f"[SLOT] {label} | OK ({elapsed:.0f}ms)")
                return result
            except Exception as e:
                tb = traceback.format_exc()
                logger(f"[SLOT] {label} | ERROR: {e}\n{tb}")
                if DEBUG:
                    parent = None
                    for arg in args:
                        if hasattr(arg, 'parent'):
                            try: parent = arg.parent()
                            except Exception: pass
                            break
                    QMessageBox.critical(parent, "Erreur",
                        f"[{label}]\n\n{type(e).__name__}: {e}")
        return wrapper
    return decorator
```

### Utilisation standard

```python
from larccommon.safe_slot import safe_slot, set_debug

# Dans main()
set_debug(True)   # Dev
set_debug(False)  # Prod

class StudentForm(QWidget):
    def __init__(self):
        super().__init__()
        self.btn_save = M3Button("Enregistrer")
        self.btn_save.clicked.connect(self._on_save)
    
    @safe_slot("StudentForm.btn_save")
    def _on_save(self):
        # Pas de try/except ici — safe_slot s'en charge
        self._save_to_db()
```

## 4. Exemples

### Exemple 1 — Lambda → slot nommé

```python
# ❌ AVANT
btn.clicked.connect(lambda: self.save(x, y))

# ✅ APRÈS
btn.clicked.connect(lambda checked, x=x, y=y: self._on_save(x, y))

@safe_slot("Form.on_save")
def _on_save(self, x, y):
    ...
```

### Exemple 2 — Extraction fichier > 1000 lignes

```
# ❌ main_window.py (1725 lignes) — INTERDIT

# ✅ Découpage :
# views/main_window.py          ← Orchestrateur (< 300 lignes)
# views/core/data_loader.py     ← Requêtes DB
# views/panels/group_panel.py   ← Stats groupe
# views/panels/student_detail.py← Détail élève
# views/dialogs/event_generator.py ← Wizard événements
```

### Exemple 3 — QWidget → ThemedWidget

```python
# ❌ AVANT — fond QSS invisible
class MonPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {p.surface};")  # ne s'affiche pas!

# ✅ APRÈS
from larccommon.widgets.themed_widget import ThemedWidget
class MonPanel(ThemedWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {p.surface};")  # OK — WA_StyledBackground actif
```

## 5. Step by Step — Mise à niveau d'une app

| Ordre | Action |
|---|---|
| 1 | `set_debug(True)` dans `main()` |
| 2 | Décorer tous les slots avec `@safe_slot("label")` |
| 3 | Remplacer les `lambda:` nus par des slots nommés |
| 4 | Vérifier `setModal(True)` sur tous les `M3Dialog` |
| 5 | Remplacer `QWidget()` par `ThemedWidget()` si QSS background |
| 6 | Vérifier chaque fichier < 1000 lignes |
| 7 | Fractionner les fichiers > 500 lignes |
| 8 | `python scripts/lint_safe_slot.py --dir .\MonApp` → 0 violation |
| 9 | `python scripts/lint_file_size.py --dir .\MonApp` → 0 violation |
| 10 | `set_debug(False)` en production |

## 6. Checklist

- [ ] `safe_slot` importé dans toutes les apps
- [ ] 0 handler sans `@safe_slot`
- [ ] 0 `lambda:` nu dans les `connect()`
- [ ] 0 `except Exception: pass` muet
- [ ] 0 `print()` dans les handlers
- [ ] 0 variable nommée `_` (écrase i18n)
- [ ] Tous les `M3Dialog` ont `setModal(True)`
- [ ] Tous les `QWidget()` avec QSS background → `ThemedWidget()`
- [ ] Aucun fichier > 1000 lignes
- [ ] Fichiers > 500 lignes examinés pour fractionnement
- [ ] `python scripts/lint_safe_slot.py` → 0 violation
- [ ] `python scripts/lint_file_size.py` → 0 violation

## Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — Tokens ds.* pour A6/A7
- **[color-rules](../color-rules/SKILL.md)** — Palette pour les couleurs
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _STYLE pour C7 (ThemedWidget)
- **[sidebar-spec](../sidebar-spec/SKILL.md)** — Spécification du sidebar (QssHelper)
- **[testing](../testing/SKILL.md)** — Tests des slots @safe_slot
