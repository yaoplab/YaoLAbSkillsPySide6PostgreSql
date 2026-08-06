---
skill: auth-intranet
version: "1.0"
priority: P0
category: infrastructure
depends_on: []
applies_to: [LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub]
linters: [lint_auth_checker.py]
reviewers: []
subsystems: [A, B, C, D]
---

# Skill: Auth Intranet — PostgreSQL Local

## 0. Contexte

**Projet** : Larc (Superviseur, Secretaire, Prof, Hub)
**Module** : `LarcCommon/larccommon/auth.py` → `AuthManager`
**Utilisateurs** : Tous (superviseurs, secrétaires, profs, coordinateurs)
**Dépendances** : `config.ini` section `[IntranetDatabase]`, `session.py`, `database.py`

Ce skill couvre l'authentification **email + mot de passe** contre la base PostgreSQL locale. C'est le mode principal quand on est sur le réseau de l'école.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Email + mot de passe saisis dans LoginWindow
**Sortie** : `AuthResult` avec `user_id`, `email`, `full_name`, `role`, `term_id`, `term_label`, `fk_language`
**Traitement** :
1. Vérifier `db.server_conn` connecté en mode INTRANET
2. Hasher le mot de passe (SHA-256)
3. Requête `larcauth_aecuser` → email + password_hash
4. Requête rôles → type_director, type_coordonator, type_supervisor, type_secretary
5. Déduire le `UserRole` (ADMIN > COORD > SECR > SUPERVISEUR > PROF)
6. Charger le terme actif via `_load_active_term()`
7. Charger la langue préférée (`fk_language`)
8. Retourner `AuthResult`

## 2. Contraintes Fondamentales

### Sous-système A — Rôles utilisateurs

| Rôle | Flag PostgreSQL | Priorité | Accès |
|---|---|---|---|
| `ADMIN` | `type_director = TRUE` | 1 (max) | Tout |
| `COORD` | `type_coordonator = TRUE` | 2 | Coordination |
| `SECR` | `type_secretary = TRUE` | 3 | Secrétariat |
| `SUPERVISEUR` | `type_supervisor = TRUE` | 4 | Supervision |
| `PROF` | Aucun flag | 5 (défaut) | Saisie des événements |

**Logique de déduction** (`_deduce_role()`) :
```python
if is_adm:       → ADMIN
elif is_coord:   → COORD
elif is_secretary: → SECR
elif is_sup:     → SUPERVISEUR
else:            → PROF
```

### Sous-système B — Hashage mot de passe

```python
def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()
```

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| Stocker le mot de passe en clair | `password_hash` = SHA-256 hex |
| Comparer les mots de passe en clair | `stored_hash == _sha256_hex(password_input)` |
| Transmettre le mot de passe en clair au serveur | Hashé côté client avant envoi |

**⚠️ Note de sécurité** : SHA-256 sans sel n'est pas idéal pour du stockage de mots de passe. Migration recommandée vers bcrypt/argon2.

### Sous-système C — Session après auth

```python
from larccommon.session import session, ConnMode

# Remplir la session (LoginWindow)
session.user_id = auth_result.user_id
session.email = auth_result.email
session.full_name = auth_result.full_name
session.role = auth_result.role
session.term_id = auth_result.term_id
session.term_label = auth_result.term_label
session.fk_language = auth_result.fk_language
session.is_authenticated = True
session.conn_mode = ConnMode.INTRANET
```

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| Modifier `session` hors de LoginWindow/PreferencesDialog | Toute modification dans `_on_intranet()` ou `_on_login_success()` |
| `session.is_authenticated = True` sans avoir vérifié le mot de passe | Vérifier `ok == True` avant de remplir la session |
| Oublier `session.conn_mode` | Toujours définir `ConnMode.INTRANET` ou `ConnMode.OFFLINE` |

### Sous-système D — Terme actif

```sql
-- Chargé automatiquement par _load_active_term()
SELECT t.id, t.label
FROM larcauth_term t, larcauth_academicyear ay
WHERE ay.s_id = 1 AND t.trim = ay.current_term_number
LIMIT 1
```

Si aucun terme trouvé → fallback : dernier terme par `ORDER BY id DESC`.

## 3. Code complet

### AuthManager.auth_intranet()

```python
from larccommon.auth import AuthManager
from larccommon.database import db, DBMode

# Vérifier la connexion
if not db.is_server_connected or db.server_mode != DBMode.INTRANET:
    return  # Pas connecté à l'intranet

ok, auth_result, error = AuthManager.auth_intranet(email, password)
if ok:
    # Remplir la session
    session.user_id = auth_result.user_id
    session.email = auth_result.email
    session.full_name = auth_result.full_name
    session.role = auth_result.role
    session.term_id = auth_result.term_id
    session.term_label = auth_result.term_label
    session.fk_language = auth_result.fk_language
    session.is_authenticated = True
    session.conn_mode = ConnMode.INTRANET
else:
    # Afficher l'erreur
    M3Snackbar.show(self, error, theme_manager.phi_theme)
```

### Tables impliquées

```sql
-- larcauth_aecuser : utilisateurs
--   id, email, last_name, first_name, password (SHA-256 hex)
--   type_director, type_coordonator, type_supervisor, type_secretary (boolean)
--   fk_language (2=fr, 1=en)

-- larcauth_term : trimestres
--   id, label, trim (numéro)

-- larcauth_academicyear : années scolaires
--   s_id=1 (ligne unique), current_term_number
```

## 4. Exemples

### Exemple 1 — Login réussi (PROF)

```python
>>> ok, result, err = AuthManager.auth_intranet("prof@arc-en-ciel.org", "monmotdepasse")
>>> ok
True
>>> result.role
<UserRole.PROF: 'PROF'>
>>> result.term_label
'1er Trimestre'
```

### Exemple 2 — Login échoué

```python
>>> ok, result, err = AuthManager.auth_intranet("inconnu@test.org", "xxx")
>>> ok
False
>>> err
'Utilisateur introuvable'
```

### Exemple 3 — Login hors intranet

```python
# Si db.server_mode != DBMode.INTRANET
>>> ok, result, err = AuthManager.auth_intranet("prof@arc-en-ciel.org", "...")
>>> ok
False
>>> err
"Non connecté à l'intranet"
```

## 5. Step by Step — Déboguer auth intranet

| Ordre | Action |
|---|---|
| 1 | Vérifier `[IntranetDatabase]` dans `config.ini` — Host, Port, DB, User, Pass |
| 2 | Vérifier `db.server_conn is not None` et `db.server_mode == DBMode.INTRANET` |
| 3 | Vérifier que l'utilisateur existe dans `larcauth_aecuser` |
| 4 | Vérifier que `password_hash` correspond (SHA-256 du mot de passe saisi) |
| 5 | Vérifier les flags rôle (au moins un TRUE ou rôle = PROF par défaut) |
| 6 | Vérifier que `larcauth_academicyear` a `s_id=1` avec `current_term_number` valide |

## 6. Checklist

- [ ] `db.server_conn` est connecté en mode `DBMode.INTRANET`
- [ ] Email trouvé dans `larcauth_aecuser` (LOWER(email) = input)
- [ ] `password_hash` correspond au SHA-256 du mot de passe saisi
- [ ] Rôle déduit correctement : ADMIN > COORD > SECR > SUPERVISEUR > PROF
- [ ] `_load_active_term()` retourne un terme valide
- [ ] `fk_language` chargé (2=fr par défaut)
- [ ] Session remplie : user_id, email, full_name, role, term_id, term_label, fk_language
- [ ] `session.conn_mode = ConnMode.INTRANET`
- [ ] `session.is_authenticated = True`
- [ ] En cas d'échec : message d'erreur affiché, session NON modifiée
- [ ] Aucun mot de passe en clair dans les logs

## Références croisées

- **[auth-oauth2](../auth-oauth2/SKILL.md)** — Auth Google OAuth2 pour superviseurs (mode alternatif)
- **[pyside6-wrapper](../pyside6-wrapper/SKILL.md)** — @safe_slot pour les handlers de login
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — LoginWindow exempté de D6 (thème figé avant affichage)
