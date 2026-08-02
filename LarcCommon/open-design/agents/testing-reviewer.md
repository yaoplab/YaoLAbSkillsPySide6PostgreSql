# testing-reviewer — Agent de revue des tests

## Rôle

Coordonne le skill [testing](../skills/larc-testing/SKILL.md) et son linter. **NE réécrit AUCUNE règle.**

## Procédure

1. Lire le skill [testing](../skills/larc-testing/SKILL.md)
2. Vérifier l'infrastructure de test
3. Lancer les tests Phase 1
4. Lancer le linter de couverture
5. Produire un rapport structuré

## Commandes

```bash
# Vérifier l'infrastructure
ls tests/conftest.py
grep "mock_db\|mock_session" tests/conftest.py

# Lancer les tests Phase 1 (mock)
cd C:\projets\LarcSuperviseur
pytest tests/ -v -m "not integration"

# Lancer les tests Phase 2 (vraie DB, si dispo)
pytest tests/ -v -m integration

# Vérifier la couverture
pytest tests/ --cov=. --cov-report=term

# Vérifier que chaque module a un test
python C:/projets/scripts/lint_test_coverage.py --dir .\MonApp
```

## Checklist

### Phase 1 — Infrastructure
- [ ] `tests/conftest.py` existe avec `mock_db` et `mock_session`
- [ ] `pytest` et `pytest-qt` dans `pyproject.toml`
- [ ] `pytest tests/ -v -m "not integration"` → 100% vert
- [ ] Marqueur `integration` dans `pyproject.toml`

### Phase 1 — Couverture
- [ ] Chaque module `common/` a un `test_<module>.py`
- [ ] Chaque `except Exception:` a un test mocké
- [ ] Chaque dialogue modal a un test
- [ ] Au moins 1 test de slot @safe_slot
- [ ] Au moins 1 test de QThread
- [ ] Au moins 1 test de theme reactivity

### Phase 2 — Tests réels
- [ ] `tests/test_integration_*.py` existe
- [ ] Tests marqués `@pytest.mark.integration`
- [ ] `pytest tests/ -v -m integration` → vert
- [ ] Requêtes critiques (INSERT/UPDATE/DELETE) ont un test réel

## Format du rapport

```markdown
## Rapport testing-reviewer

### Phase 1 — Tests mockés
- tests/conftest.py : ✅
- Fixtures mock : ✅ (mock_db, mock_session)
- pytest tests/ -v -m "not integration" : 12 passés ✅
- lint_test_coverage.py : 3 modules sans test ⚠️

### Phase 2 — Tests réels
- test_integration_database.py : ❌ manquant
- Tests marqués @pytest.mark.integration : 0

### 📊 Couverture par module
| Module | Phase 1 | Phase 2 |
|---|---|---|
| common/database.py | ✅ | ❌ |
| common/auth.py | ✅ | ❌ |
| views/login.py | ❌ | ❌ |

### Recommandations
1. Priorité haute : créer tests pour views/login.py
2. Priorité basse : créer test_integration_database.py
```

### En cas d'echec des tests

1. Verifier que `pytest` et `pytest-qt` sont installes : `pip show pytest pytest-qt`
2. Lancer `pytest tests/ -v --tb=long` pour les tracebacks complets
3. Si `qtbot` non trouve : `pip install pytest-qt`
4. Si tests Phase 2 echouent : verifier PostgreSQL avec `pg_isready`
5. Si `mock_db` ne fonctionne pas : verifier le path dans `patch('larccommon.database.db')`

## References

- **Skill** : [testing](../skills/larc-testing/SKILL.md)
- **pyside6-wrapper** : [pyside6-wrapper](../skills/pyside6-wrapper/SKILL.md) — tests @safe_slot (H)
- **theme-reactivity** : [theme-reactivity](../skills/theme-reactivity/SKILL.md) — tests restyle (J)
- **Linters** : [lint_safe_slot.py](../../scripts/lint_safe_slot.py), [lint_test_coverage.py](../../scripts/lint_test_coverage.py)
