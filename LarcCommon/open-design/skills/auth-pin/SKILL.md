---
skill: auth-pin
version: "1.0"
priority: P1
category: infrastructure
depends_on: [auth-intranet]
applies_to: [LarcProf]
linters: [lint_auth_checker.py]
reviewers: []
subsystems: [A, B, C, D]
---

# Skill: Auth PIN — Jeton hors connexion

## 0. Contexte

**Projet** : LarcProf
**Module** : `LarcCommon/larccommon/auth.py` → `AuthManager.auth_pin()`, `LarcProf/common/sqlite_init.py`
**Utilisateurs** : Professeurs (mode hors connexion)
**Dépendances** : SQLite local (`session_cache`), `auth-intranet` (setup initial)

Ce skill couvre l'authentification par **code PIN** pour les professeurs. Le PIN est un code à 4-8 chiffres, défini par le professeur au premier login, stocké localement en SQLite. Il permet de se connecter **sans** PostgreSQL — utile quand le serveur intranet est inaccessible ou que le professeur est en déplacement.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Email + PIN (4-8 chiffres) saisis dans LoginWindow (onglet PIN)
**Sortie** : `AuthResult` avec `user_id`, `email`, `full_name`, `role`, `term_id`, `term_label`
**Traitement** :
1. Hasher le PIN (SHA-256)
2. Requête SQLite locale `session_cache` → email + pin_hash
3. Retourner les données de session mises en cache
4. Mode = `ConnMode.OFFLINE`

## 2. Contraintes Fondamentales

### Sous-système A — Cycle de vie du PIN

```
┌─────────────────────────────────────────────────────┐
│ 1. PREMIER LOGIN (Intranet ou Google)               │
│    Le professeur s'authentifie AVEC le serveur      │
│    ↓                                                │
│ 2. CRÉATION DU PIN                                  │
│    _ask_pin_setup() → boîte de dialogue             │
│    "Définissez un PIN pour <nom>"                   │
│    PIN : 4-8 chiffres                               │
│    ↓                                                │
│ 3. STOCKAGE LOCAL                                   │
│    sqlite_init.save_session(result, pin)            │
│    → INSERT INTO session_cache                      │
│    (user_id, email, full_name, role, term_id,       │
│     term_label, pin_hash, updated_at)               │
│    ↓                                                │
│ 4. LOGIN HORS CONNEXION                             │
│    AuthManager.auth_pin(email, pin)                 │
│    → SELECT FROM session_cache WHERE pin_hash = ?   │
│    → ConnMode.OFFLINE                               │
│    ↓                                                │
│ 5. CHANGEMENT DE PIN                                │
│    ChangePinDialog → sqlite_init.save_session()     │
│    → UPDATE session_cache SET pin_hash = ?          │
└─────────────────────────────────────────────────────┘
```

| # | Contrainte | Gravité |
|---|---|---|
| A1 | **Premier login OBLIGATOIREMENT via Intranet ou OAuth2** — le PIN ne peut PAS être le premier mode d'auth | 🔴 P0 |
| A2 | **PIN = 4 à 8 chiffres** — `isdigit()` + `4 <= len <= 8` | 🔴 P0 |
| A3 | **PIN hashé SHA-256** avant stockage — jamais en clair | 🔴 P0 |
| A4 | **Session locale = copie de la session serveur** — `user_id`, `email`, `full_name`, `role`, `term_id`, `term_label` | 🔴 P0 |
| A5 | **Mode = OFFLINE** — `session.conn_mode = ConnMode.OFFLINE` après auth PIN | 🟡 P1 |
| A6 | **Le PIN peut être renouvelé** — `ChangePinDialog` ou reset par nouveau login Intranet | 🟡 P1 |

### Sous-système B — Base SQLite locale

```sql
-- LarcProf crée automatiquement session_cache.db
CREATE TABLE IF NOT EXISTS session_cache (
    user_id    INTEGER PRIMARY KEY,
    email      TEXT NOT NULL,
    full_name  TEXT,
    role       TEXT,
    term_id    INTEGER,
    term_label TEXT,
    pin_hash   TEXT,
    updated_at TEXT
);
```

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| Stocker le PIN en clair | `pin_hash = SHA-256(pin)` |
| Recréer la table à chaque démarrage | `CREATE TABLE IF NOT EXISTS` |
| Utiliser `session_cache` comme source de vérité | Ce n'est qu'un cache — la source est PostgreSQL |

### Sous-système C — AuthManager.auth_pin()

```python
@classmethod
def auth_pin(cls, email: str, pin: str, local_conn=None) -> Tuple[bool, AuthResult, str]:
    if local_conn is None:
        return False, AuthResult(), 'Base locale non disponible'
    pin_hash = _sha256_hex(pin)
    try:
        row = local_conn.execute(
            "SELECT user_id, email, full_name, role, term_id, term_label "
            "FROM session_cache WHERE LOWER(email) = ? AND pin_hash = ?",
            (email.strip().lower(), pin_hash)
        ).fetchone()
        if row is None:
            return False, AuthResult(), 'Email ou PIN incorrect'
        return True, AuthResult(
            user_id=int(row['user_id']),
            email=row['email'],
            full_name=row['full_name'],
            role=UserRole(row['role']),
            term_id=int(row['term_id'] or 0),
            term_label=row['term_label'] or '',
        ), ''
    except Exception as e:
        return False, AuthResult(), str(e)
```

| Étape | Description |
|---|---|
| 1 | Vérifier que `local_conn` (SQLite) n'est pas None |
| 2 | Hasher le PIN fourni |
| 3 | Chercher l'email + le hash dans `session_cache` |
| 4 | Si trouvé → `AuthResult` avec les données du cache |
| 5 | Si non trouvé → "Email ou PIN incorrect" |

### Sous-système D — ChangePinDialog

```python
# LarcProf/views/password.py
class ChangePinDialog(QDialog):
    def _on_accept(self):
        new_pin = self._pin_edit.text().strip()
        if not new_pin or not new_pin.isdigit() or len(new_pin) < 4 or len(new_pin) > 8:
            self._show_error('Le PIN doit contenir 4 à 8 chiffres.')
            return
        from common.sqlite_init import sqlite_init
        from common.session import session
        sqlite_init.save_session(session, new_pin)
        QMessageBox.information(self, 'Succès', 'PIN mis à jour avec succès.')
        self.accept()
```

## 3. Code complet

### Premier login → création PIN (LoginWindow LarcProf)

```python
# Après auth_intranet() ou OAuth2 réussi
if mode in (ConnMode.INTRANET, ConnMode.CLOUD) and not skip_pin:
    pin, ok = self._ask_pin_setup(res.full_name)
    sqlite_init.save_session(res, pin if ok else "")

def _ask_pin_setup(self, name: str):
    text, ok = QInputDialog.getText(
        self, "PIN hors connexion",
        f"Définissez un PIN pour {name} (laisser vide pour ignorer) :",
        QLineEdit.Password
    )
    if ok and text and text.isdigit() and 4 <= len(text) <= 8:
        return text, True
    return "", False
```

### Login hors connexion (onglet PIN)

```python
@safe_slot("LoginWindow.on_pin")
def _on_pin(self):
    email = self._edt_p_email.text().strip()
    pin = self._edt_p_pin.text()
    if not email or not pin:
        self._show_error("Veuillez saisir votre email et votre PIN.")
        return
    # Lancer dans un thread pour ne pas bloquer l'UI
    self._worker = _Worker(AuthManager.auth_pin, email, pin, parent=self)
    self._worker.done.connect(self._on_auth_pin_done)
    self._worker.start()
```

## 4. Exemples

### Exemple 1 — Premier setup du PIN

```
1. Prof se connecte en Intranet → succès
2. Boîte de dialogue : "Définissez un PIN pour Marie Dupont"
3. Prof saisit "123456" → SHA-256 → stocké dans session_cache
4. Prochaine ouverture de LarcProf → onglet PIN disponible
```

### Exemple 2 — Login PIN réussi (hors connexion)

```python
>>> ok, result, err = AuthManager.auth_pin("marie@arc-en-ciel.org", "123456", local_conn=sqlite_conn)
>>> ok
True
>>> result.role
<UserRole.PROF: 'PROF'>
>>> session.conn_mode = ConnMode.OFFLINE
```

### Exemple 3 — PIN invalide

```python
>>> ok, result, err = AuthManager.auth_pin("marie@arc-en-ciel.org", "0000", local_conn=sqlite_conn)
>>> ok
False
>>> err
'Email ou PIN incorrect'
```

## 5. Step by Step — Déboguer le PIN

| Ordre | Action |
|---|---|
| 1 | Vérifier que `session_cache.db` existe dans le dossier de l'app |
| 2 | Vérifier que l'utilisateur a fait un premier login Intranet réussi |
| 3 | Vérifier que `save_session()` a été appelé (log ou breakpoint) |
| 4 | Vérifier que `pin_hash` dans SQLite correspond au SHA-256 du PIN saisi |
| 5 | Vérifier que `local_conn` est passé à `auth_pin()` (pas None) |
| 6 | Vérifier que `ConnMode.OFFLINE` est activé après auth PIN |

## 6. Checklist

- [ ] Premier login via Intranet ou OAuth2 avant toute utilisation du PIN
- [ ] PIN = 4 à 8 chiffres (`isdigit()`, longueur 4-8)
- [ ] PIN hashé SHA-256 avant stockage
- [ ] `session_cache` table créée avec `CREATE TABLE IF NOT EXISTS`
- [ ] `save_session()` appelé après premier login réussi
- [ ] `save_session()` appelé après changement de PIN
- [ ] `auth_pin()` vérifie `local_conn is not None` avant de requêter
- [ ] `session.conn_mode = ConnMode.OFFLINE` après auth PIN réussie
- [ ] `_ask_pin_setup()` permet de laisser vide (skip PIN)
- [ ] `ChangePinDialog` modal avec validation (4-8 chiffres)
- [ ] UI : onglet PIN avec `QLineEdit.Password` (echo masqué)
- [ ] UI : bouton "Changer le PIN" accessible depuis l'onglet PIN
- [ ] Traductions i18n : `prof_login.pin_title`, `prof_login.pin_placeholder`, `prof_login.pin_note`, `prof_login.connect_pin`, `prof_login.change_pin`, `prof_login.tab_pin`

### Vérification

```bash
# Vérifier que la table session_cache existe
sqlite3 session_cache.db ".tables"

# Vérifier le hashage SHA-256 (doit matcher)
python -c "import hashlib; print(hashlib.sha256('123456'.encode()).hexdigest())"
```

## Références croisées

- **[auth-intranet](../auth-intranet/SKILL.md)** — Auth PostgreSQL (étape 1 : setup initial du PIN)
- **[auth-oauth2](../auth-oauth2/SKILL.md)** — Auth Google (alternative étape 1)
- **[pyside6-wrapper](../pyside6-wrapper/SKILL.md)** — @safe_slot pour `_on_pin()`
- **[testing](../testing/SKILL.md)** — Tests du flux PIN (mock SQLite)
