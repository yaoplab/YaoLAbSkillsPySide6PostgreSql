---
name: design-review
description: Audit complet du design system Larc - tokens, couleurs, hardcoding, reactivite au theme
category: quality
trigger: audit design, verifie le design, check design, revue design, design review
---

# Design Review - Audit Design System Larc

Lancer les 3 linters design et produire un rapport consolide.

## Procedure

1. Lancer les linters :
```bash
python C:/projets/scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4+D5+D6+D7 --fix-only
python C:/projets/scripts/lint_qss_hardcoding.py --fix-only
python C:/projets/scripts/audit_theme_reactive.py
```

2. Pour chaque violation, mapper vers la regle du skill :
   - D1 -> color-rules : couleur explicite manquante
   - D3 -> color-rules : hex hardcode
   - R1-R16 -> zero-hardcoding : px en dur
   - J1-J7 -> theme-reactivity : theme non reactif
   - K1-K25 -> sidebar-spec : sidebar non conforme

3. Proposer la correction en citant la regle.

## Skills de reference
- design-tokens, color-rules, zero-hardcoding, theme-reactivity
- sidebar-spec, ergonomics, card-dashboard, student-record
