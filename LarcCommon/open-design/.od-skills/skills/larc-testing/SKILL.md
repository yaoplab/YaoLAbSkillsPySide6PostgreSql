---
skill: testing
version: "1.0"
priority: P1
category: quality
depends_on: [pyside6-wrapper]
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcCommon]
linters: [lint_test_coverage.py]
reviewers: [testing-reviewer]
subsystems: [A, B, C, D, E, F, G, H, I, J]
---

# Skill: Testing

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof, Hub, Common)
**Framework** : pytest + pytest-qt + unittest.mock
**Utilisateurs** : Tous les développeurs Larc
**Dépendances** : `pytest>=9`, `pytest-qt>=4`, `psycopg2`

## 1. Fonction Principale

### Type : Système Ouvert

**Entrée** : Code Python PySide6 avec connexions PostgreSQL
**Sortie** : Tests pytest validant le comportement avec et sans base de données réelle
**Traitement** : Stratégie en 2 phases — Phase 1 (mock) obligatoire, Phase 2 (réel) recommandée

## 2. Stratégie en 2 phases (contraintes)

### Phase 1 — Tests unitaires avec mock (OBLIGATOIRE)

Tests rapides, sans dépendance externe. Pour :
- Tester la logique métier (sans DB)
- Tester les cas d'erreur
- Tester les dialogues et vues (pytest-qt)
- Permettre à tout développeur de lancer les tests

### Phase 2 — Tests d'intégration avec vraie DB (RECOMMANDÉ)

Pour :
- Vérifier la syntaxe SQL réelle
- Vérifier les contraintes PostgreSQL
- Valider les procédures stockées

> **RÈGLE ABSOLUE** : Phase 1 100% verte avant d'écrire Phase 2.
> Test réel échoue + mocké passe → SQL réel invalide.
> Test mocké échoue + réel passe → mock mal configuré.

## 2. Contraintes Fondamentales

| # | Contrainte | Phase |
|---|---|---|
| C1 | Tout module `common/` DOIT avoir des tests mockés | 1 | 🔴 P0 |
| C2 | Tests mockés passent sans PostgreSQL | 1 | 🔴 P0 |
| C3 | Tests UI utilisent `pytest-qt` avec `qtbot` | 1 | 🔴 P0 |
| C4 | ≥ 1 test par méthode publique | 1+2 | 🟡 P1 |
| C5 | Tests intégration DB dans `test_integration_*.py` | 2 | 🟡 P1 |
| C6 | Tests Phase 2 marqués `@pytest.mark.integration` | 2 | 🟡 P1 |

### ❌/✅ Anti-patterns

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| Test qui dépend de l'ordre d'exécution | Chaque test indépendant (fixtures) |
| `time.sleep()` dans les tests | `qtbot.waitSignal()` ou `qtbot.wait(ms)` |
| Test sans `try/finally` pour session globale | Toujours restaurer `session.is_authenticated`, `session.role` |
| Test Phase 2 sans `@pytest.mark.integration` | Marquer TOUS les tests réels |

## 3. Code complet
| C2 | Tests mockés passent sans PostgreSQL | 1 |
| C3 | Tests UI utilisent `pytest-qt` avec `qtbot` | 1 |
| C4 | ≥ 1 test par méthode publique | 1+2 |
| C5 | Tests intégration DB dans `test_integration_*.py` | 2 |
| C6 | Tests Phase 2 marqués `@pytest.mark.integration` | 2 |

### Sous-système A — Fixtures Mock

```python
# tests/conftest.py
@pytest.fixture
def mock_db():
    with patch('larccommon.database.db') as mock:
        mock.server_conn = MagicMock()
        mock.is_server_connected = True
        mock.server_conn.cursor.return_value.__enter__.return_value = MagicMock()
        mock.server_mode = MagicMock()
        yield mock

@pytest.fixture
def mock_session():
    with patch('larccommon.session.session') as mock:
        mock.user_id = 1
        mock.display_name = "Test User"
        mock.is_authenticated = True
        mock.role = MagicMock()
        yield mock
```

### Sous-système B — pytest-qt pour les vues

```python
def test_button_click(qtbot, mock_db):
    widget = MyWidget()
    qtbot.addWidget(widget)
    widget.show()
    qtbot.mouseClick(widget.btn_save, Qt.LeftButton)
    mock_db.server_conn.cursor.assert_called_once()
```

### Sous-système C — Phase 2 (vraie DB)

```python
@pytest.mark.integration
class TestDatabase:
    def test_connexion_intranet(self):
        from larccommon.database import db
        assert db.connect_intranet() == True
        assert db.server_conn is not None

    def test_chargement_classes(self):
        from larccommon.database import db
        db.connect_intranet()
        cur = db.server_conn.cursor()
        cur.execute("SELECT COUNT(*) FROM larcauth_classroom WHERE enabled = TRUE")
        assert cur.fetchone()[0] > 0
```

### Sous-système D — Structure

```
app/tests/
├── conftest.py                    # Fixtures Phase 1
├── test_database.py               # Phase 1 mock
├── test_auth.py                   # Phase 1 mock
├── test_views.py                  # Phase 1 pytest-qt
├── test_sync.py                   # Phase 1 mock
├── test_integration_database.py   # Phase 2 réelle
└── test_integration_views.py      # Phase 2 réelle
```

### Sous-système E — Configuration pytest

```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short --strict-markers"
markers = ["integration: tests requiring a real PostgreSQL database"]
```

### Sous-système F — Règles de couverture

| # | Règle | Phase |
|---|---|---|
| F1 | Chaque `if ... raise` a un test mocké | 1 |
| F2 | Chaque `except Exception:` a un test mocké | 1 |
| F3 | Requêtes SQL critiques (INSERT/UPDATE/DELETE) ont un test réel | 2 |
| F4 | Chaque dialogue modal a un test pytest-qt | 1 |

### Sous-système G — Exécution sélective

```bash
pytest tests/ -v -m "not integration"     # Phase 1 uniquement
pytest tests/ -v -m integration            # Phase 2 uniquement
pytest tests/ -v                           # Tout
```

### Sous-système H — Tests des slots @safe_slot

```python
from unittest.mock import patch

def test_slot_error_handled(qtbot, app):
    """Un slot décoré @safe_slot ne crashe pas l'application."""
    widget = SignExplorer()
    qtbot.addWidget(widget)
    with patch.object(widget, '_operation_risquee', side_effect=ValueError("test")):
        widget._btn_risque.click()
        # Pas d'exception = test OK

def test_slot_label_obligatoire():
    """Vérifier que tous les slots ont un label @safe_slot."""
    # Le linter lint_safe_slot.py vérifie ceci statiquement
    pass
```

### Sous-système I — Tests des QThread

```python
def test_preloader_signals(qtbot):
    """PhotoPreloader émet progress et done."""
    from larccommon.photos import PhotoPreloader
    preloader = PhotoPreloader(["id1", "id2"])
    with qtbot.waitSignal(preloader.done, timeout=5000):
        preloader.start()

def test_batch_processor(qtbot, mock_db):
    """BatchProcessor traite les signes sans erreur."""
    from larccommon.batch_processor import BatchProcessor
    processor = BatchProcessor([{"sign_id": "1", "gardiner_code": "A1"}], provider="ollama")
    with qtbot.waitSignal(processor.finished, timeout=10000):
        processor.start()
```

### Sous-système J — Tests de theme reactivity

```python
def test_theme_change_emet_signal(qtbot, app):
    """set_active émet theme_changed."""
    from larccommon.theme import theme_manager
    original = theme_manager.active_name
    try:
        with qtbot.waitSignal(theme_manager.theme_changed, timeout=1000):
            theme_manager.set_active("dark")
    finally:
        theme_manager.set_active(original)

def test_restyle_all_appele(qtbot, app):
    """_restyle_all est appelé lors du changement de thème."""
    widget = MaVue()
    qtbot.addWidget(widget)
    with patch.object(widget, '_restyle_all', wraps=widget._restyle_all) as spy:
        theme_manager.set_active("dark")
        spy.assert_called_once()
```

## 4. Exemples

### Exemple 0 — Test avant/après

```python
# ❌ AVANT : pas de test, le bug passe en production
def save_student(name, classroom_id):
    db.execute("INSERT INTO student (name, cid) VALUES (?, ?)", (name, classroom_id))

# ✅ APRÈS : test mocké vérifie l'appel SQL
def test_save_student(mock_db):
    mock_cursor = mock_db.server_conn.cursor.return_value.__enter__.return_value
    save_student("Marie", 5)
    mock_cursor.execute.assert_called_once()
    args = mock_cursor.execute.call_args[0]
    assert "INSERT INTO student" in args[0]
```

### Exemple 1 — Phase 1 : DataLoader mocké

```python
def test_get_student_classroom(mock_db):
    mock_cursor = mock_db.server_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = (1, "Classe A")
    from views.core.data_loader import DataLoader
    result = DataLoader().get_student_classroom(123)
    assert result["classroom_id"] == 1
    mock_cursor.execute.assert_called_once()
```

### Exemple 2 — Phase 2 : DataLoader réel

```python
@pytest.mark.integration
def test_get_student_classroom_reel():
    from larccommon.database import db
    db.connect_intranet()
    from views.core.data_loader import DataLoader
    result = DataLoader().get_student_classroom(1)
    assert result is not None
```

### Exemple 3 — Test de session (sans mock)

```python
def test_authenticated_user(qtbot, app):
    from larccommon.session import session, UserRole
    orig_auth, orig_role = session.is_authenticated, session.role
    try:
        session.is_authenticated = True
        session.role = UserRole.CONTRIBUTEUR
        widget = MaVue()
        qtbot.addWidget(widget)
        assert widget._btn_edit.isVisible()
    finally:
        session.is_authenticated = orig_auth
        session.role = orig_role
```

## 5. Step by Step

### Phase 1 (prioritaire)

| Ordre | Action |
|---|---|
| 1 | Créer `tests/conftest.py` avec fixtures mock |
| 2 | Créer `tests/test_database.py` (1 test/méthode) |
| 3 | Créer `tests/test_views.py` avec pytest-qt |
| 4 | Ajouter `pytest` et `pytest-qt` aux dépendances |
| 5 | `pytest tests/ -v -m "not integration"` → 100% vert |
| 6 | `pytest --cov` → ≥ 60% couverture |

### Phase 2 (quand DB dispo)

| Ordre | Action |
|---|---|
| 7 | Créer `tests/test_integration_database.py` |
| 8 | Marquer avec `@pytest.mark.integration` |
| 9 | `pytest tests/ -v -m integration` → vert |

## 6. Checklist

### Phase 1
- [ ] `tests/conftest.py` existe avec `mock_db` et `mock_session`
- [ ] `pytest` et `pytest-qt` dans `pyproject.toml`
- [ ] `pytest tests/ -v -m "not integration"` → 100% vert
- [ ] Chaque `except Exception:` a un test mocké (F2)
- [ ] Chaque dialogue modal a un test (F4)
- [ ] Couverture ≥ 60%
- [ ] Au moins 1 test de slot @safe_slot (H)
- [ ] Au moins 1 test de QThread (I)
- [ ] Au moins 1 test de theme reactivity (J)

### Phase 2
- [ ] `tests/test_integration_*.py` existe
- [ ] Marqueur `integration` configuré dans `pyproject.toml`
- [ ] `pytest tests/ -v -m integration` → vert
- [ ] Requêtes critiques (INSERT/UPDATE/DELETE) ont un test réel (F3)

### Vérification
- [ ] `python scripts/lint_test_coverage.py` → 0 module sans test

## Références croisées

- **[pyside6-wrapper](../pyside6-wrapper/SKILL.md)** — @safe_slot (testé en H)
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — Pattern _restyle_all (testé en J)
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — Règles vérifiables par linter
