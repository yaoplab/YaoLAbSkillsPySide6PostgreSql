---
name: feature-review
description: Audit des fonctionnalites - evenements, vignettes, dossier eleve, widgets
category: quality
trigger: audit feature, verifie feature, check feature, revue feature, evenements, event generator, vignettes, card dashboard, dossier eleve
---

# Feature Review - Audit Fonctionnalites Larc

Verifier la conformite design des fonctionnalites metier.

## Procedure

1. Lancer les linters design :
```bash
python C:/projets/scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4+D5+D6+D7 --fix-only
python C:/projets/scripts/lint_qss_hardcoding.py --fix-only
```

2. Audit specifique :
```bash
# Event Generator
grep -rn "event_color\|event_icon" views/ | grep -v test_
# Card Dashboard
grep -rn "CardFields\|CARD_SECRETAIRE\|CARD_SUPERVISEUR\|CARD_PROF" views/
# Student Record
grep -rn "notes_json\|dossier_panel\|student_form" views/
# Widgets bruts (dette technique)
grep -rn "QPushButton\|QLineEdit\|QComboBox\|QTableWidget" --include="*.py" views/
```

## Checklist (toutes features)
- [ ] 0 couleur hex hardcodee
- [ ] 0 px en dur
- [ ] theme_changed -> _restyle_all() dans chaque classe
- [ ] @safe_slot sur tous les handlers
- [ ] ThemedWidget pour conteneurs avec QSS background
- [ ] Traductions i18n pour tous les textes

## Skills de reference
- event-generator, card-dashboard, student-record, toolkit-reference
