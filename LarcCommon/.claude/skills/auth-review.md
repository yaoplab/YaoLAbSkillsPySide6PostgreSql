---
name: auth-review
description: Audit de l authentification - OAuth2 Google, PostgreSQL local, PIN hors connexion
category: quality
trigger: audit auth, verifie auth, check auth, revue auth, authentification, login, OAuth
---

# Auth Review - Audit Authentification Larc

Verifier la configuration et la securite des 3 modes d authentification.

## Procedure

1. Lancer les linters :
```bash
python C:/projets/scripts/lint_auth_checker.py
python C:/projets/scripts/lint_db_checker.py
```

2. Verifier la configuration :
```bash
grep -A2 "\[OAuth2\]" LarcCommon/config.ini
grep -A5 "\[IntranetDatabase\]" LarcCommon/config.ini
```

3. Tester la connexion :
```bash
python -c "from larccommon.database import db; print('INTRANET OK' if db.connect_intranet() else 'INTRANET FAIL')"
```

## Checklist

### OAuth2
- [ ] [OAuth2] ClientID et ClientSecret dans config.ini
- [ ] URI http://localhost:8765/callback autorisee Google Console
- [ ] Domaine arc-en-ciel.org (hd)
- [ ] Timeout 120s
- [ ] Utilisateur dans larcauth_aecuser
- [ ] Flag role non NULL

### Intranet
- [ ] [IntranetDatabase] Host/Port/DB/User/Pass dans config.ini
- [ ] db.connect_intranet() -> True
- [ ] Password hash = SHA-256
- [ ] session.conn_mode = ConnMode.INTRANET

### PIN
- [ ] session_cache.db existe
- [ ] Premier login Intranet/OAuth2 AVANT PIN
- [ ] PIN = 4-8 chiffres, isdigit()
- [ ] pin_hash = SHA-256
- [ ] session.conn_mode = ConnMode.OFFLINE

## Skills de reference

- auth-oauth2, auth-intranet, auth-pin, database-operations
