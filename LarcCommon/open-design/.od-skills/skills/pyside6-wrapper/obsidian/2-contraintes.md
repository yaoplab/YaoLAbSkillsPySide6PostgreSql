---
tags:
  - skill
  - pyside6-wrapper
  - contrainte
---

# Contraintes

| # | Contrainte |
|---|---|
| C1 | Tout slot connecté à un signal est décoré avec `@safe_slot("App.section.action")` |
| C2 | Aucun `lambda:` nu dans les `connect()` |
| C3 | `set_debug(True)` en dev, `set_debug(False)` en prod |
| C4 | Label unique et descriptif |

## Anti-patterns Qt

| ❌ Ancien | ✅ Nouveau |
|---|---|
| `button.clicked.connect(lambda: self.save())` | `button.clicked.connect(self._on_save)` avec `@safe_slot` |
| `try: ... except: pass` | `@safe_slot` gère l'exception |
| `print()` dans handlers | `log()` via `@safe_slot` |
