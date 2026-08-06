# auth-reviewer — Agent de revue Authentification

## Role

Coordonne les 3 skills auth et leurs linters. **NE reecrit AUCUNE regle.**

## Procedure

1. Lire le skill correspondant au mode d'auth audite
2. Lancer le linter auth + db (les deux sont lies)
3. Verifier la configuration `config.ini`
4. Produire un rapport structure

## Mapping perimetre -> skills + linters

| Perimetre | Skill | Linter |
|---|---|---|
| Auth Google OAuth2 | [auth-oauth2](../skills/auth-oauth2/SKILL.md) | `python C:/projets/scripts/lint_auth_checker.py --dir .\LarcSuperviseur` |
| Auth PostgreSQL local | [auth-intranet](../skills/auth-intranet/SKILL.md) | `python C:/projets/scripts/lint_auth_checker.py` + `python C:/projets/scripts/lint_db_checker.py` |
| Auth PIN hors connexion | [auth-pin](../skills/auth-pin/SKILL.md) | `python C:/projets/scripts/lint_auth_checker.py --dir .\LarcProf` |

## Commandes

```bash
# Audit complet auth (tous projets)
python C:/projets/scripts/lint_auth_checker.py
python C:/projets/scripts/lint_db_checker.py

# Verification config OAuth2
grep -A2 "\[OAuth2\]" LarcCommon/config.ini

# Verification config Intranet
grep -A5 "\[IntranetDatabase\]" LarcCommon/config.ini

# Verification session_cache SQLite (LarcProf)
python -c "import sqlite3; conn=sqlite3.connect('session_cache.db'); print(conn.execute('SELECT COUNT(*) FROM session_cache').fetchone()[0])"

# Test connexion intranet
python -c "from larccommon.database import db; print('OK' if db.connect_intranet() else 'FAIL')"
```

## Checklist

### OAuth2
- [ ] `[OAuth2]` ClientID et ClientSecret dans `config.ini`
- [ ] URI `http://localhost:8765/callback` autorisee dans Google Console
- [ ] Domaine restreint a `arc-en-ciel.org` (`hd` parameter)
- [ ] Callback < 120s (timeout)
- [ ] Utilisateur existe dans `larcauth_aecuser`
- [ ] Flag role (director/coordinator/supervisor) non NULL

### Intranet
- [ ] `[IntranetDatabase]` Host/Port/DB/User/Pass dans `config.ini`
- [ ] `db.connect_intranet()` retourne True
- [ ] `db.server_conn is not None`
- [ ] `db.server_mode == DBMode.INTRANET`
- [ ] Password hash = SHA-256 (pas de clair)
- [ ] `session.conn_mode = ConnMode.INTRANET` apres auth

### PIN
- [ ] `session_cache.db` existe (SQLite)
- [ ] Premier login via Intranet ou OAuth2 AVANT utilisation PIN
- [ ] PIN = 4-8 chiffres, `isdigit()`
- [ ] `pin_hash` = SHA-256, jamais en clair
- [ ] `session.conn_mode = ConnMode.OFFLINE` apres auth PIN

## Format du rapport

```markdown
## Rapport auth-reviewer

### Config
- config.ini [OAuth2] : ClientID=... OK
- config.ini [IntranetDatabase] : Host=127.0.0.1 OK
- db.connect_intranet() : True

### Linter
- lint_auth_checker.py : 0 P0, 2 P1
- lint_db_checker.py : 0 P0, 1 P1

### Violations
| Fichier | Ligne | Regle | Correction |
|---|---|---|---|
| reset_pwd.py | 2 | db-C1 | Supprimer import psycopg2, utiliser db |
| reset_pwd.py | 8 | db-C4 | Remplacer psycopg2.connect par db.connect_intranet |
```

### En cas d'echec

1. **`config.ini` introuvable** : verifier `LarcCommon/config.ini` existe
2. **`db.connect_intranet()` echoue** : verifier PostgreSQL (`pg_isready`), port dans config.ini
3. **OAuth2 timeout** : verifier que le port 8765 n'est pas bloque (firewall)
4. **`session_cache.db` manquant** (PIN) : l'utilisateur n'a pas fait de premier login Intranet
5. **Linter auth ne trouve rien mais le code a des credentials** : lancer SANS `--dir` pour scanner tous les projets

## References

- [auth-oauth2](../skills/auth-oauth2/SKILL.md)
- [auth-intranet](../skills/auth-intranet/SKILL.md)
- [auth-pin](../skills/auth-pin/SKILL.md)
- [database-operations](../skills/database-operations/SKILL.md)
- [pyside6-wrapper](../skills/pyside6-wrapper/SKILL.md) — @safe_slot pour les handlers login
