"""Accès DB + JSON pour LarcDesign."""
import json, os, hashlib
from larccommon.database import db

L10N_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'LarcCommon', 'larccommon', 'l10n'))
FR_PATH = os.path.join(L10N_DIR, 'fr.json')
EN_PATH = os.path.join(L10N_DIR, 'en.json')


def load_json(lang='fr'):
    p = FR_PATH if lang == 'fr' else EN_PATH
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def save_json(data, lang='fr'):
    p = FR_PATH if lang == 'fr' else EN_PATH
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _conn():
    c = db.server_conn
    if not c:
        db.connect_intranet()
        c = db.server_conn
    return c


def get_roles():
    c = _conn()
    if not c:
        return []
    try:
        cur = c.cursor()
        cur.execute("""
            SELECT id, last_name, first_name, email,
                   type_supervisor, type_coordonator, type_secretary, is_adm
            FROM larcauth_aecuser ORDER BY last_name
        """)
        rows = []
        for r in cur.fetchall():
            roles = []
            if r[7]: roles.append('Admin')
            if r[5]: roles.append('Coord')
            if r[4]: roles.append('Superviseur')
            if r[6]: roles.append('Secretaire')
            rows.append({
                'id': r[0], 'last_name': r[1], 'first_name': r[2],
                'email': r[3], 'roles': ', '.join(roles) if roles else '—'
            })
        return rows
    except:
        return []


def get_event_types():
    c = _conn()
    if not c:
        return []
    try:
        cur = c.cursor()
        cur.execute("""
            SELECT idtypeevent, type_event, "Event_Niveau2", "Event_Niveau3", "Enabled"
            FROM larcauth_type_event ORDER BY idtypeevent
        """)
        return [dict(zip(['id', 'cat', 'niv2', 'niv3', 'enabled'], r)) for r in cur.fetchall()]
    except:
        return []


def get_locations():
    c = _conn()
    if not c:
        return []
    try:
        cur = c.cursor()
        cur.execute("SELECT id, fk_etablissement, nom_lieu FROM larcauth_lieu ORDER BY nom_lieu")
        return [dict(zip(['id', 'fk_etab', 'nom'], r)) for r in cur.fetchall()]
    except:
        return []


def get_logs(limit=200):
    c = _conn()
    if not c:
        return []
    try:
        cur = c.cursor()
        cur.execute("""
            SELECT id, secretary_name, action, target_type, target_id, detail, created_at
            FROM audit_trail ORDER BY created_at DESC LIMIT %s
        """, (limit,))
        return [dict(zip(['id', 'user', 'action', 'target_type', 'target_id', 'detail', 'at'], r))
                for r in cur.fetchall()]
    except:
        return []
