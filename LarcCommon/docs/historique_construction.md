
# Historique de construction — LarcCommon

## Itération 1 — Création (22 juin 2026)

### Problème initial
Les applications Larc (LarcSuperviseur, LarcSecretaire, etc.) partagent
des modules d'infrastructure (DB, auth, logger, theme) mais chaque projet
a sa propre copie de `common/`. Pas de bibliothèque UI commune.

### Décision
Créer `LarcCommon` comme dépôt central :

1. **phibuilder/** — UI toolkit Material Design 3 + Fibonacci
   - Déplacé depuis l'ancien `LarcPhibuilder`
   - 12 widgets M3, génération QSS, thème dynamique
   - 51 tests passants

2. **larccommon/** — Infrastructure partagée
   - Modules copiés depuis `LarcSuperviseur/common/`
   - Ajout du module `l10n/` pour les traductions multilingues
   - `theme.py` modifié pour intégrer `PhiBuilder` (QSS M3 global)

3. **LarcSuperviseur/common/** — Modules passerelle
   - Chaque fichier réexporte depuis `larccommon.modules`
   - Aucune modification des vues nécessaire
   - `top_bar.py` modifié : vignettes colorées pour les thèmes

4. **5 thèmes** : Océan, Forêt, Nuit, Lave, Sable
   - Utilisent PhiBuilder/materialyoucolor pour le QSS M3
   - Palettes manuelles pour compatibilité ascendante

### Prochaines itérations
- Traductions dans les vues (intégration l10n)
- Refactoring UI avec phibuilder widgets
- Nettoyage ancien dépôt LarcPhibuilder
