---
skill: auth-oauth2
version: "1.0"
priority: P0
category: infrastructure
depends_on: []
applies_to: [LarcSuperviseur]
linters: [lint_auth_checker.py]
reviewers: []
subsystems: [A, B, C]
---

# Skill: Auth OAuth2 — Google Workspace

## 0. Contexte

**Projet** : LarcSuperviseur
**Module** : `LarcCommon/larccommon/auth.py` → `OAuth2Manager`
**Utilisateurs** : Superviseurs, coordinateurs, administrateurs
**Domaine** : `@arc-en-ciel.org` (Google Workspace)
**Dépendances** : `config.ini` section `[OAuth2]`, `session.py`

Ce skill couvre l'authentification **Google OAuth2 PKCE** pour le personnel d'encadrement.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Clic sur "Connexion Google" dans LoginWindow
**Sortie** : `AuthResult` avec `user_id`, `email`, `full_name`, `role`, `term_id`, `term_label`
**Traitement** :
1. Générer PKCE (verifier + challenge + state)
2. Ouvrir le navigateur → Google OAuth2 consent screen
3. Attendre le callback HTTP sur `localhost:8765/callback`
4. Échanger le code contre un token (Google API)
5. Décoder le JWT `id_token` → email + name
6. Vérifier le domaine `hd == 'arc-en-ciel.org'`
7. Chercher l'utilisateur dans PostgreSQL → rôle superviseur/coord/admin
8. Retourner `AuthResult`

## 2. Contraintes Fondamentales

### Sous-système A — Configuration OAuth2

```ini
# config.ini
[OAuth2]
ClientID=<google-client-id>.apps.googleusercontent.com
ClientSecret=<google-client-secret>
```

| ❌ Interdit | ✅ Obligatoire |
|---|---|
| `ClientID` vide | Remplir depuis Google Cloud Console |
| `ClientSecret` vide | Remplir depuis Google Cloud Console |
| URI de redirection arbitraire | `http://localhost:8765/callback` (port fixe) |

**Port** : `8765` — codé en dur dans `OAuth2Manager.PORT`. Ne pas modifier sans mettre à jour Google Console.

### Sous-système B — Flow PKCE

```
1. Génération
   verifier  = base64url(32 octets aléatoires)
   challenge = base64url(SHA-256(verifier))
   state     = base64url(16 octets aléatoires)

2. Redirection navigateur
   https://accounts.google.com/o/oauth2/v2/auth?
     client_id=...
     &redirect_uri=http://localhost:8765/callback
     &response_type=code
     &scope=openid email profile
     &code_challenge=...
     &code_challenge_method=S256
     &state=...
     &hd=arc-en-ciel.org
     &access_type=offline
     &prompt=select_account

3. Callback HTTP
   GET http://localhost:8765/callback?code=<code>&state=<state>
   → _CallbackHandler extrait le code
   → Réponse HTML "Authentification réussie"
   → event.set() débloque le thread principal

4. Échange de token
   POST https://oauth2.googleapis.com/token
   Body: code + client_id + client_secret + redirect_uri + grant_type=authorization_code + code_verifier
   → Réponse: { id_token, access_token, ... }

5. Décodage JWT (sans bibliothèque)
   id_token = "header.payload.signature"
   payload = base64_decode(payload_part)
   → email, name, hd (hosted domain)
```

| # | Contrainte | Gravité |
|---|---|---|
| B1 | **Domaine obligatoire** — `hd` DOIT être `arc-en-ciel.org` | 🔴 P0 |
| B2 | **Timeout 120s** — l'utilisateur a 2 minutes pour s'authentifier | 🟡 P1 |
| B3 | **State vérifié** — anti-CSRF (actuellement généré mais pas revérifié au callback — à corriger) | 🟡 P1 |
| B4 | **HTTPServer daemon** — thread daemon, ne bloque pas la sortie | 🟡 P1 |
| B5 | **Code unique** — le callback handler utilise des variables de classe (non thread-safe si 2 auth simultanées) | 🟡 P1 |

### Sous-système C — Résolution du rôle

L'utilisateur Google doit exister dans PostgreSQL (`larcauth_aecuser`) ET avoir un rôle d'encadrement.

| Colonne PostgreSQL | Signification |
|---|---|
| `type_director` | Administrateur → `UserRole.ADMIN` |
| `type_coordonator` | Coordinateur → `UserRole.COORD` |
| `type_supervisor` | Superviseur → `UserRole.SUPERVISEUR` |

**Règle absolue** : Si l'utilisateur n'a AUCUN des 3 flags → accès refusé ("Accès réservé aux superviseurs, coordinateurs et administrateurs.")

## 3. Code complet

### OAuth2Manager.authenticate()

```python
from larccommon.auth import OAuth2Manager

ok, auth_result, error = OAuth2Manager.authenticate()
if ok:
    # auth_result.user_id, .email, .full_name, .role
    # .term_id, .term_label, .fk_language
    session.user_id = auth_result.user_id
    session.email = auth_result.email
    session.full_name = auth_result.full_name
    session.role = auth_result.role
    session.term_id = auth_result.term_id
    session.term_label = auth_result.term_label
    session.is_authenticated = True
else:
    M3Snackbar.show(self, f"Échec OAuth2 : {error}", theme_manager.phi_theme)
```

### Configuration Google Cloud Console

```
1. Créer un projet → https://console.cloud.google.com
2. APIs & Services → Credentials → Create OAuth 2.0 Client ID
3. Type: Web application
4. Authorized redirect URIs: http://localhost:8765/callback
5. Copier ClientID et ClientSecret → config.ini
```

## 4. Exemples

### Exemple 1 — LoginWindow intégration

```python
class LoginWindow(QWidget):
    @safe_slot("LoginWindow.on_google")
    def _on_google(self):
        self._google_btn.setEnabled(False)
        ok, result, err = OAuth2Manager.authenticate()
        if ok:
            self._apply_session(result)
            self._open_main_window()
        else:
            if err:
                M3Snackbar.show(self, err, theme_manager.phi_theme)
        self._google_btn.setEnabled(True)
```

### Exemple 2 — Erreur domaine non autorisé

```python
# Si l'utilisateur se connecte avec @gmail.com au lieu de @arc-en-ciel.org
# → "Domaine non autorisé : gmail.com"
# Solution : utiliser le compte Workspace (@arc-en-ciel.org)
```

## 5. Step by Step — Déboguer OAuth2

| Ordre | Action |
|---|---|
| 1 | Vérifier `[OAuth2]` ClientID/ClientSecret dans `config.ini` |
| 2 | Vérifier que `http://localhost:8765/callback` est dans les URIs autorisées Google Console |
| 3 | Vérifier que le port 8765 n'est pas bloqué (firewall) |
| 4 | Vérifier que l'utilisateur a un compte @arc-en-ciel.org |
| 5 | Vérifier que l'utilisateur existe dans `larcauth_aecuser` |
| 6 | Vérifier que `type_director`/`type_coordonator`/`type_supervisor` n'est pas NULL |

## 6. Checklist

- [ ] `[OAuth2]` ClientID et ClientSecret configurés dans `config.ini`
- [ ] URI de redirection `http://localhost:8765/callback` autorisée dans Google Console
- [ ] Domaine restreint à `arc-en-ciel.org` (hd)
- [ ] Callback reçu dans les 120 secondes (timeout)
- [ ] JWT id_token décodé et vérifié
- [ ] Utilisateur trouvé dans `larcauth_aecuser`
- [ ] Au moins un flag rôle (director/coordinator/supervisor) = True
- [ ] Session remplie après succès : user_id, email, full_name, role, term_id, term_label
- [ ] `_deduce_role_superviseur()` correct : ADMIN > COORD > SUPERVISEUR
- [ ] `_load_active_term()` charge le terme courant de l'année scolaire active

## Références croisées

- **[auth-intranet](../auth-intranet/SKILL.md)** — Auth PostgreSQL pour les professeurs (mode alternatif)
- **[pyside6-wrapper](../pyside6-wrapper/SKILL.md)** — @safe_slot pour les handlers de login
- **[theme-reactivity](../theme-reactivity/SKILL.md)** — LoginWindow n'a pas besoin de theme_changed (exempté D6)
