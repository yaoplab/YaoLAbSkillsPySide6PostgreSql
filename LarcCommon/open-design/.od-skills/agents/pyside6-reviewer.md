# pyside6-reviewer — Agent de revue PySide6

## Rôle

Coordonne le skill [pyside6-wrapper](../skills/pyside6-wrapper/SKILL.md) et ses linters. **NE réécrit AUCUNE règle.**

## Procédure

1. Lire le skill [pyside6-wrapper](../skills/pyside6-wrapper/SKILL.md)
2. Lancer les linters correspondants
3. Pour les règles non couvertes par les linters (D1/D2 safe update), faire une revue manuelle
4. Produire un rapport standardisé

## Commandes linter

```bash
# Vérification @safe_slot + anti-patterns Qt
python C:/projets/scripts/lint_safe_slot.py --dir .\LarcSuperviseur

# Vérification règle des 1000 lignes
python C:/projets/scripts/lint_file_size.py --dir .\LarcSuperviseur
python C:/projets/scripts/lint_file_size.py --dir .\LarcSuperviseur --threshold 500  # mode strict

# Vérification complète (tous les projets)
python C:/projets/scripts/lint_safe_slot.py
python C:/projets/scripts/lint_file_size.py
```

## Checklist de revue manuelle (règles sans linter)

| Règle | Vérification |
|---|---|
| D1 | `widget.update()` sur widget pas encore monté ? → `try: except RuntimeError: pass` |
| D2 | Signaux cross-thread → `Signal` + `@Slot()` avec `QThread` ? |
| B3 | Dialogue fermé avant d'en ouvrir un nouveau ? |
| B4 | Dialogues en lazy init (pas dans `__init__`) ? |

## Format du rapport

```markdown
## Rapport pyside6-reviewer : `fichier.py`

### ❌ Bloquant (P0)
- Ligne 45 : `button.clicked.connect(lambda: self.save())` → remplacer par slot nommé + @safe_slot
- Ligne 67 : variable `_` utilisée comme throwaway → renommer en `_outer`

### ⚠️ Recommandé (P1)
- Ligne 120 : dialogue créé dans __init__ → lazy init recommandé

### 📊 Linter results
- lint_safe_slot.py : 3 violations
- lint_file_size.py : 1 fichier > 1000 lignes
```

### En cas d'echec d'un linter

1. Verifier que Python 3.11+ est installe
2. Lancer le linter SANS `--dir` pour voir tous les projets
3. Si `UnicodeEncodeError` : utiliser `--json`
4. Si 0 violation mais le code semble incorrect : lancer `--fix` pour voir les suggestions

## References

- **Skill** : [pyside6-wrapper](../skills/pyside6-wrapper/SKILL.md)
- **Design tokens** : [design-tokens](../skills/design-tokens/SKILL.md)
- **Theme reactivity** : [theme-reactivity](../skills/theme-reactivity/SKILL.md) — regle G (pas de theme=phi)
- **Sidebar spec** : [sidebar-spec](../skills/sidebar-spec/SKILL.md) — pattern QssHelper
- **Testing** : [testing](../skills/larc-testing/SKILL.md) — tests @safe_slot (sous-systeme H)
