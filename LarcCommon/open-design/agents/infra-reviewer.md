# infra-reviewer — Agent de revue Infrastructure

## Role

Coordonne les skills infrastructure (database, sync) et leurs linters. **NE reecrit AUCUNE regle.**

## Procedure

1. Lire [database-operations](../skills/database-operations/SKILL.md) et [sync](../skills/sync/SKILL.md)
2. Verifier les connexions PostgreSQL
3. Lancer les linters
4. Tester la synchronisation (si LarcCloudSync)
5. Produire un rapport

## Mapping perimetre -> skills + linters

| Perimetre | Skill | Linter |
|---|---|---|
| Connexion DB | [database-operations](../skills/database-operations/SKILL.md) | `python C:/projets/scripts/lint_db_checker.py` |
| Synchronisation | [sync](../skills/sync/SKILL.md) | `python C:/projets/scripts/lint_db_checker.py` |
| Auth (partage db) | [auth-intranet](../skills/auth-intranet/SKILL.md) | `python C:/projets/scripts/lint_auth_checker.py` |

## Commandes

```bash
# Audit complet infrastructure
python C:/projets/scripts/lint_db_checker.py --json
python C:/projets/scripts/lint_auth_checker.py --json

# Verification connexion locale
python -c "
from larccommon.database import db, DBMode
ok = db.connect_intranet()
print(f'Intranet: {\"OK\" if ok else \"FAIL\"} (mode={db.server_mode})')
"

# Verification connexion cloud
python -c "
from larccommon.database import db
ok = db.connect_cloud()
print(f'Cloud: {\"OK\" if ok else \"FAIL\"} (mode={db.server_mode})')
"

# Test sync (si LarcCloudSync est configure)
python -c "
from thothcommon.sync import sync_manager
print(sync_manager.sync_table('larcauth_aecuser'))
"

# Stats fichiers (>500 lignes)
python C:/projets/scripts/lint_file_size.py --stats
```

## Checklist

### Database
- [ ] `[IntranetDatabase]` et `[SupabaseDatabase]` dans `config.ini`
- [ ] `db.connect_intranet()` → True
- [ ] `db.server_conn is not None`
- [ ] 0 `import psycopg2` hors de `database.py`
- [ ] 0 `psycopg2.connect()` direct hors de `database.py`
- [ ] `is_server_connected` verifie avant chaque requete
- [ ] Cursor utilise avec `with` (context manager)
- [ ] `disconnect_all()` appele a la fermeture

### Sync
- [ ] Connexion locale + cloud fonctionnelles
- [ ] `sync_version` present dans les tables synchronisees
- [ ] `ON CONFLICT DO NOTHING` sur les INSERT
- [ ] `sslmode='require'` sur la connexion cloud
- [ ] Logs par table apres chaque sync
- [ ] Mode degrade si cloud inaccessible

## Format du rapport

```markdown
## Rapport infra-reviewer

### Connexions
- Intranet (127.0.0.1:5432) : OK
- Cloud (Supabase:6543) : OK

### Linter
- lint_db_checker.py : 0 P0, 3 P1
- lint_auth_checker.py : 0 P0, 0 P1

### Sync
- larcauth_aecuser : A jour
- larcauth_classroom : 2 enr. local -> cloud

### Violations
| Fichier | Regle | Correction |
|---|---|---|
| views/data_loader.py | db-C3 | Ajouter is_server_connected check |
```

### En cas d'echec

1. **`db.connect_intranet()` = False** : verifier `pg_isready`, Host/Port dans `config.ini`
2. **`db.connect_cloud()` = False** : verifier Supabase credentials, connexion internet
3. **Sync echoue** : verifier que les deux connexions sont OK, lancer `sync_table` table par table
4. **`sync_version` manquant** : verifier le schema SQL — la colonne doit exister dans chaque table
5. **Linter db ne trouve rien** : lancer avec `--json` pour voir les P1 (warning)

## References

- [database-operations](../skills/database-operations/SKILL.md)
- [sync](../skills/sync/SKILL.md)
- [auth-intranet](../skills/auth-intranet/SKILL.md)
