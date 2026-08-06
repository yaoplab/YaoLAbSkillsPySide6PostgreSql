---
tags:
  - skill
  - pyside6-wrapper
  - exemple
  - exemple-simple
---

# Exemples

## Exemple 1 — Bouton simple

```python
@safe_slot("MainWindow.btn_export_pdf")
def _on_export_pdf(self):
    pdf = QPrinter()
    doc = QTextDocument()
    doc.setHtml(self._build_html())
    doc.print_(pdf)
```

## Exemple 2 — Table avec modification

```python
@safe_slot("StudentTable.on_item_change")
def _on_item_change(self, item: QTableWidgetItem):
    self._update_student_field(item.row(), item.column(), item.text())
```
