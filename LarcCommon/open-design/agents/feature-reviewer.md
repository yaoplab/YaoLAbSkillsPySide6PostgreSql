# feature-reviewer — Agent de revue Fonctionnalites

## Role

Coordonne les skills fonctionnels (event-generator, card-dashboard, student-record) et leurs linters. **NE reecrit AUCUNE regle.**

## Procedure

1. Identifier la fonctionnalite concernee
2. Lire le skill correspondant
3. Lancer les linters design (commun a toutes les features)
4. Verifier les regles specifiques a la feature
5. Produire un rapport

## Mapping perimetre -> skills + linters

| Perimetre | Skill | Linter |
|---|---|---|
| Wizard evenements | [event-generator](../skills/event-generator/SKILL.md) | `python C:/projets/scripts/lint_d1_color_checker.py` + `python C:/projets/scripts/lint_qss_hardcoding.py` |
| Vignettes eleves | [card-dashboard](../skills/card-dashboard/SKILL.md) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| Dossier eleve | [student-record](../skills/student-record/SKILL.md) | `lint_d1_color_checker.py` + `lint_qss_hardcoding.py` |
| Catalogue widgets | [toolkit-reference](../skills/toolkit-reference/SKILL.md) | `lint_qss_hardcoding.py --dir .\LarcCommon` |

## Commandes

```bash
# Audit design (commun a toutes les features)
python C:/projets/scripts/lint_d1_color_checker.py --rule D1+J7+D3+D4+D5+D6+D7 --fix-only
python C:/projets/scripts/lint_qss_hardcoding.py --fix-only

# Audit specifique event-generator
grep -rn "event_color\|event_icon" LarcSuperviseur/views/ LarcCommon/larccommon/ | grep -v test_

# Audit specifique card-dashboard
grep -rn "CardFields\|CARD_SECRETAIRE\|CARD_SUPERVISEUR\|CARD_PROF" LarcSuperviseur/views/ LarcSecretaire/views/

# Audit specifique student-record
grep -rn "notes_json\|dossier_panel\|student_form" LarcSecretaire/views/

# Verification catalogue widgets
grep -rn "QPushButton\|QLineEdit\|QComboBox\|QTableWidget" --include="*.py" LarcSuperviseur/views/ LarcSecretaire/views/ LarcProf/views/
```

## Checklist

### Toutes features
- [ ] 0 couleur hex hardcodee — `lint_d1_color_checker.py` → 0 violation
- [ ] 0 px en dur — `lint_qss_hardcoding.py` → 0 violation
- [ ] `theme_changed` connecte → `_restyle_all()` dans chaque classe
- [ ] `@safe_slot` sur tous les handlers
- [ ] `ThemedWidget` pour les conteneurs avec QSS background
- [ ] Traductions i18n pour tous les textes visibles

### Event Generator
- [ ] 3 modes disponibles (Absence, Retard, Evenements)
- [ ] `event_color()` utilise des tokens palette (pas hex)
- [ ] `event_icon()` utilise Unicode, pas PNG

### Card Dashboard
- [ ] `CardFields` configure par role (pas de champs en dur)
- [ ] Etats visuels (7 etats) fonctionnels
- [ ] Pastille de presence avec token palette
- [ ] Info-bulle au survol (`setToolTip`)

### Student Record
- [ ] 6 categories + 6 sections documentaires
- [ ] Dialogue adaptatif par type d'entree
- [ ] Badges de statut colores
- [ ] Timeline chronologique fonctionnelle

## Format du rapport

```markdown
## Rapport feature-reviewer : [fonctionnalite]

### Linter
- lint_d1_color_checker.py : X violations
- lint_qss_hardcoding.py : X violations

### Checklist feature
- [x] 0 hex hardcode
- [x] theme_changed connecte
- [ ] event_color() encore en hex -> migration planifiee

### Violations
| Fichier | Ligne | Regle | Correction |
|---|---|---|---|
| event_helpers.py | 17 | D3 | Remplacer '#27ae60' par '{p.success}' |
```

### En cas d'echec

1. **Les linters design ne trouvent rien** : verifier que `--fix-only` n'est pas utilise (masque les warnings)
2. **`grep` ne trouve pas `QPushButton`** : le code utilise peut-etre deja `M3Button` — tant mieux
3. **`event_color()` contient des hex** : dette technique connue, migration planifiee vers tokens palette
4. **`CardFields` non trouve** : le code utilise peut-etre l'ancienne `StudentCard` sans configuration

## References

- [event-generator](../skills/event-generator/SKILL.md)
- [card-dashboard](../skills/card-dashboard/SKILL.md)
- [student-record](../skills/student-record/SKILL.md)
- [toolkit-reference](../skills/toolkit-reference/SKILL.md)
- [design-tokens](../skills/design-tokens/SKILL.md)
- [color-rules](../skills/color-rules/SKILL.md)
