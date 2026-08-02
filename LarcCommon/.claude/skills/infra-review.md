---
name: infra-review
description: Audit de l infrastructure - base de donnees, synchronisation local-cloud
category: quality
trigger: audit infra, verifie infra, check infra, revue infra, base de donnees, synchronisation, sync
---

# Infra Review - Audit Infrastructure Larc

Verifier les connexions PostgreSQL et la synchronisation.

## Procedure

1. Lancer les linters :
```bash
python C:/projets/scripts/lint_db_checker.py --json
python C:/projets/scripts/lint_auth_checker.py --json
python C:/projets/scripts/lint_file_size.py --stats
```

2. Tester les connexions :
```bash
python -c "from larccommon.database import db; print('INTRANET OK' if db.connect_intranet() else 'FAIL')"
```

3. Tester la synchronisation (si LarcCloudSync) :
```bash
python -c "from thothcommon.sync import sync_manager; print(sync_manager.sync_table('larcauth_aecuser'))"
```

## Checklist Database
- [ ] [IntranetDatabase] et [SupabaseDatabase] dans config.ini
- [ ] db.connect_intranet() -> True
- [ ] 0 import psycopg2 hors de database.py
- [ ] 0 psycopg2.connect() direct
- [ ] is_server_connected verifie avant requete
- [ ] disconnect_all() a la fermeture

## Checklist Sync
- [ ] Connexion locale + cloud OK
- [ ] sync_version present
- [ ] ON CONFLICT DO NOTHING sur INSERT
- [ ] sslmode=require sur cloud
- [ ] Mode degrade si cloud inaccessible

## Skills de reference

- database-operations, sync, auth-intranet
