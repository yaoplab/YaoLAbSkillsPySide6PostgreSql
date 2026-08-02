---
skill: database-operations
version: "1.0"
priority: P0
category: infrastructure
depends_on: []
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcCommon]
linters: [lint_db_checker.py]
reviewers: []
subsystems: [A, B, C, D]
---

# Skill: Database Operations

## 0. Contexte

**Projet** : Larc (toutes les apps)
**Module** : `LarcCommon/larccommon/database.py`
**Utilisateurs** : Tous les développeurs Larc
**Dépendances** : `psycopg2-binary>=2.9`, `config.ini`

Ce skill couvre le **singleton `db`** — la porte d'entrée unique vers PostgreSQL.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Besoin d'exécuter une requête SQL
**Sortie** : Connexion PostgreSQL active (`db.server_conn`)
**Traitement** : Le singleton `db` gère deux connexions (intranet + cloud) et expose la connexion active

## 2. Contraintes Fondamentales

### Sous-système A — Architecture

```
config.ini ──→ Database._pg_params() ──→ psycopg2.connect(**params)
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
            db._intranet (localhost:5432)                  db._cloud (Supabase:6543)
            DBMode.INTRANET                                DBMode.CLOUD
                    │                                               │
                    └────────── db.server_conn ─────────────────────┘
                              (propriété : retourne la connexion active)
```

| État | `db.server_mode` | `db.server_conn` retourne |
|---|---|---|
| Non connecté | `DBMode.NONE` | `None` |
| Connecté intranet | `DBMode.INTRANET` | `db._intranet` |
| Connecté cloud | `DBMode.CLOUD` | `db._cloud` |

### Sous-système B — Configuration

```ini
[IntranetDatabase]
Host=127.0.0.1
Port=5432
DB=NewLarcDB
User=postgres
Pass=postgres

[SupabaseDatabase]
Host=aws-0-eu-central-1.pooler.supabase.com
Port=6543
DB=postgres
User=postgres.yourref
Pass=your-db-password
```

### Sous-système C — Utilisation

```python
from larccommon.database import db, DBMode

# 1. Connexion (LoginWindow)
db.connect_intranet()   # → True/False
# ou
db.connect_cloud()      # → True/False (SSL requis)

# 2. Vérification OBLIGATOIRE avant toute requête
if not db.is_server_connected:
    self._show_error("Base de données inaccessible.")
    return

# 3. Requête
conn = db.server_conn
with conn.cursor() as cur:
    cur.execute("SELECT id, email FROM larcauth_aecuser WHERE id = %s", (user_id,))
    row = cur.fetchone()

# 4. Déconnexion (sortie de l'app)
db.disconnect_all()
```

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| `psycopg2.connect(...)` hors de `database.py` | Toujours utiliser `db.server_conn` |
| `db.server_conn.cursor()` sans vérifier `is_server_connected` | `if not db.is_server_connected: return` |
| `import psycopg2` dans une vue | `from larccommon.database import db` |
| Hardcoder les credentials | Lire depuis `config.ini` via `_pg_params()` |
| Instancier `Database()` | Utiliser le singleton `db` |

### Sous-système D — Modes

| Mode | Quand | Exemple |
|---|---|---|
| `DBMode.INTRANET` | Sur le réseau de l'école | PostgreSQL local |
| `DBMode.CLOUD` | Hors réseau, connexion distante | Supabase |
| `DBMode.NONE` | Aucune connexion | Appel à `connect_*()` a échoué |

**Règle** : `server_mode` est mis à jour automatiquement par `connect_intranet()`/`connect_cloud()`. Ne jamais le modifier manuellement.

**Timeout** : `connect_timeout=5` (secondes) — évite les blocages.

**Autocommit** : `True` sur les deux connexions — pas besoin de `conn.commit()`.

## 3. Code complet

```python
from larccommon.database import db, DBMode

# Pattern standard pour une vue
class MaVue(QWidget):
    def _load_data(self):
        if not db.is_server_connected:
            self._show_error("Base de données inaccessible.")
            return
        try:
            with db.server_conn.cursor() as cur:
                cur.execute("SELECT * FROM larcauth_classroom WHERE enabled = TRUE")
                return cur.fetchall()
        except Exception as e:
            log(f"Erreur chargement: {e}")
            return []
```

## 4. Exemples

### Connexion depuis LoginWindow

```python
class LoginWindow(QWidget):
    def _try_connect_intranet(self):
        if db.connect_intranet():
            self._show_intranet_tab()
        else:
            self._show_cloud_only()
```

### Erreur psycopg2 non installé

```
connect_intranet: psycopg2 non installé
→ Solution : pip install psycopg2-binary
```

## 5. Step by Step — Déboguer connexion

| Ordre | Action |
|---|---|
| 1 | Vérifier `[IntranetDatabase]` dans `config.ini` |
| 2 | Vérifier PostgreSQL en cours d'exécution (`pg_isready`) |
| 3 | Vérifier `pip show psycopg2-binary` |
| 4 | Tester `db.connect_intranet()` → True ? |
| 5 | Tester `db.server_conn` → pas None ? |

## 6. Checklist

- [ ] `db` singleton importé depuis `larccommon.database`
- [ ] 0 `import psycopg2` direct hors de `database.py`
- [ ] 0 hardcodage de credentials (Host, Port, DB, User, Pass)
- [ ] `is_server_connected` vérifié avant chaque requête
- [ ] `config.ini` sections `[IntranetDatabase]` et `[SupabaseDatabase]` configurées
- [ ] `connect_intranet()` appelé au démarrage (LoginWindow)
- [ ] `disconnect_all()` appelé à la fermeture
- [ ] Cursor utilisé avec `with` (context manager)
- [ ] `connect_timeout=5` — pas de blocage infini
- [ ] `autocommit=True` — pas de transactions non commitées

## Références croisées

- **[auth-intranet](../auth-intranet/SKILL.md)** — Utilise `db` pour l'authentification
- **[sync](../sync/SKILL.md)** — Utilise `db` pour la synchronisation
- **[testing](../testing/SKILL.md)** — Mock `db` pour les tests Phase 1
