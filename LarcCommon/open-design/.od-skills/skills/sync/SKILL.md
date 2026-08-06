---
skill: sync
version: "1.0"
priority: P1
category: infrastructure
depends_on: [database-operations]
applies_to: [LarcCloudSync, LarcSuperviseur]
linters: [lint_db_checker.py]
reviewers: []
subsystems: [A, B, C]
---

# Skill: Synchronisation Local↔Cloud

## 0. Contexte

**Projet** : LarcCloudSync
**Module** : `C:\projets\LarcCloudSync\sync_agent\sync.py`
**Utilisateurs** : Administrateurs système
**Dépendances** : `database-operations`, PostgreSQL local + Supabase cloud

Ce skill couvre la **synchronisation PostgreSQL local → Supabase cloud**. Les données sont saisies localement (intranet) puis synchronisées vers le cloud pour l'accès distant.

## 1. Fonction Principale

### Type : Système Ouvert

**Entrée** : Base PostgreSQL locale avec données modifiées
**Sortie** : Base Supabase cloud synchronisée
**Traitement** : Comparer `sync_version` local vs cloud, pousser/tirer les enregistrements modifiés

## 2. Contraintes Fondamentales

### Sous-système A — Architecture

```
┌──────────────────┐         ┌──────────────────┐
│ PostgreSQL Local │ ◄─────► │ Supabase Cloud   │
│ (Intranet)       │  sync   │ (Internet)       │
│ 127.0.0.1:5432   │         │ aws-0-...pooler  │
│ NewLarcDB        │         │ postgres:6543    │
└──────────────────┘         └──────────────────┘
        │                            │
   sync_version                sync_version
   (par ligne)                 (par ligne)
```

**Principe :** `sync_version` est une colonne entière dans chaque table. Incrémentée à chaque modification. Le côté avec la version la plus haute est la source de vérité ("leader-wins").

### Sous-système B — Algorithme

```
sync_table("nom_table"):
  1. Connexion aux deux bases (local + cloud)
  2. SELECT MAX(sync_version) → v_local, v_cloud
  3. Si v_local == v_cloud → "À jour"
  4. Si v_local > v_cloud → push local → cloud
  5. Si v_cloud > v_local → pull cloud → local
```

| État | Action | Résultat |
|---|---|---|
| `v_local == v_cloud` | Rien | "À jour" |
| `v_local > v_cloud` | `INSERT INTO cloud ... ON CONFLICT DO NOTHING` | "N enr. local → cloud" |
| `v_cloud > v_local` | `INSERT INTO local ... ON CONFLICT DO NOTHING` | "N enr. cloud → local" |

### Sous-système C — Limitations

| # | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|
| C1 | Modifier `sync_version` manuellement | Laisser le trigger PostgreSQL l'incrémenter | 🔴 P0 |
| C2 | Sync sans vérifier les connexions | Vérifier local ET cloud avant `sync_table()` | 🔴 P0 |
| C3 | Ignorer les erreurs de sync | Logger chaque échec par table | 🟡 P1 |

### Limitations connues

| Limitation | Détail |
|---|---|
| **Pas de résolution de conflit** | Si la même ligne est modifiée des deux côtés, le leader écrase l'autre |
| **Leader-wins** | Le côté avec `sync_version` le plus élevé gagne |
| **Pas de gestion des suppressions** | Soft delete recommandé (flag `deleted`) |
| **Pas de transactions distribuées** | Chaque ligne est synchronisée indépendamment |
| **ON CONFLICT DO NOTHING** | Évite les doublons mais ignore les conflits |

## 3. Code complet

### sync_table (simplifié)

```python
def sync_table(table: str) -> str:
    local_conn = psycopg2.connect(**local_params)
    cloud_conn = psycopg2.connect(**cloud_params, sslmode='require')

    v_local = max_sync_version(local_conn, table)
    v_cloud = max_sync_version(cloud_conn, table)

    if v_local == v_cloud:
        return "À jour"

    if v_local > v_cloud:
        rows = get_rows_since(local_conn, table, v_cloud)
        for row in rows:
            insert_into(cloud_conn, table, row)  # ON CONFLICT DO NOTHING
        return f"{len(rows)} enr. local → cloud"

    if v_cloud > v_local:
        rows = get_rows_since(cloud_conn, table, v_local)
        for row in rows:
            insert_into(local_conn, table, row)  # ON CONFLICT DO NOTHING
        return f"{len(rows)} enr. cloud → local"
```

### Tables synchronisées

```python
SYNC_TABLES = [
    "larcauth_aecuser",
    "larcauth_classroom",
    "larcauth_term",
    "larcauth_academicyear",
    # ...
]
```

## 4. Exemples

### Exemple 1 — Sync à jour

```python
# ❌ AVANT : les deux côtés ont sync_version=5
>>> v_local, v_cloud = 5, 5

# ✅ APRÈS : rien à synchroniser
>>> sync_manager.sync_table("larcauth_aecuser")
"À jour"
```

### Exemple 2 — Push local → cloud

```python
# ❌ AVANT : local v=7, cloud v=5 (2 modifications locales)
>>> v_local, v_cloud = 7, 5

# ✅ APRÈS : les 2 lignes modifiées sont poussées
>>> sync_manager.sync_table("larcauth_classroom")
"2 enr. local → cloud"
```

### Exemple 3 — Sync avec échec cloud

```python
>>> sync_manager.sync_table("larcauth_aecuser")
"À jour"
```

### Push local → cloud

```python
# Local : 3 modifications depuis la dernière sync
>>> sync_manager.sync_table("larcauth_classroom")
"3 enr. local → cloud"
```

### Échec de connexion cloud

```python
# Supabase inaccessible
>>> sync_manager.sync_table("larcauth_aecuser")
"Sync larcauth_aecuser: could not connect to server"
```

## 5. Step by Step — Exécuter une sync

| Ordre | Action |
|---|---|
| 1 | Vérifier connexion PostgreSQL local |
| 2 | Vérifier connexion Supabase cloud |
| 3 | Lancer `sync_all_tables(SYNC_TABLES)` |
| 4 | Vérifier les résultats par table |
| 5 | Logger les erreurs éventuelles |

## 6. Checklist

- [ ] Connexion PostgreSQL local fonctionnelle
- [ ] Connexion Supabase cloud fonctionnelle
- [ ] `sync_version` présent dans toutes les tables
- [ ] `ON CONFLICT DO NOTHING` sur les INSERT
- [ ] `sslmode='require'` sur la connexion cloud
- [ ] Résultats loggés par table
- [ ] Mode dégradé si cloud inaccessible (données locales préservées)
- [ ] Pas de soft delete implémenté (limitation connue)

### Vérification

```bash
# Tester la connexion aux deux bases
python -c "from larccommon.database import db; print(db.connect_intranet())"
python -c "from larccommon.database import db; print(db.connect_cloud())"

# Lancer une sync manuelle
python -c "from thothcommon.sync import sync_manager; print(sync_manager.sync_table('larcauth_aecuser'))"
```

## Références croisées

- **[database-operations](../database-operations/SKILL.md)** — Singleton `db` et connexions
- **[auth-intranet](../auth-intranet/SKILL.md)** — Tables `larcauth_*` synchronisées
- **[testing](../testing/SKILL.md)** — Tests Phase 2 avec vraie DB
