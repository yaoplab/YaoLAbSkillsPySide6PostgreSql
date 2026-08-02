
# LarcCommon — Instructions pour agents IA

## Règles générales
- Toujours vérifier si un module existe avant d'en créer un nouveau
- Utiliser les modules passerelle dans `LarcSuperviseur/common/` pour compatibilité
- Ne pas modifier les imports des vues LarcSuperviseur sans raison
- Préférer les clés contextuelles pour les traductions

## Commandes
```bash
# Installer en mode développement
cd C:\projets\LarcCommon
pip install -e .

# Lancer les tests
cd C:\projets\LarcCommon
pytest tests/ -v

# Lancer LarcSuperviseur
cd C:\projets
python -m LarcSuperviseur
```

## Conventions de code
- Dataclasses pour les structures de données
- Singletons pour DB, session, theme_manager, app_config
- QSS généré via StyleBuilder (pas de QSS inline dans phibuilder)
- Traductions via `_("cle.contextuelle")`
- Imports : `from larccommon.xxx import yyy`

## Structure des thèmes
Les thèmes sont définis dans `larccommon/theme.py` :
- `THEMES_CONFIG` : liste des thèmes (key, label, seed_color, is_dark)
- `_THEME_PALETTES` : palettes manuelles pour compatibilité
- `ThemeManager` : facade qui intègre PhiBuilder

Pour ajouter un thème :
1. Ajouter une entrée dans `THEMES_CONFIG`
2. Ajouter une `Palette` dans `_THEME_PALETTES`
3. Les tests et le sélecteur UI s'adaptent automatiquement
