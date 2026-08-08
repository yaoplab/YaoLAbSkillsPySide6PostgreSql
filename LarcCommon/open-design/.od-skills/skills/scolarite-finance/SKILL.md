---
skill: scolarite-finance
version: "1.0"
priority: P0
category: feature
depends_on: [design-tokens, color-rules, zero-hardcoding, dashboard-pattern, search-detail-pattern]
applies_to: [LarcCompta]
linters: [lint_qss_hardcoding.py, lint_d1_color_checker.py]
reviewers: [feature-reviewer, design-reviewer]
subsystems: [SF, S1, S2, S3, S4, S5]
---

# Skill: Scolarité Finance — Gestion des Frais de Scolarité

## 0. Contexte

**Projet** : LarcScolarité (LarcCompta)
**Module** : `LarcCompta/views/` — dashboard, parents_list, class_payment_panel, fee_config, reminders
**Utilisateurs** : Comptables, gestionnaires, directeurs financiers
**Dépendances** : `design-tokens`, `color-rules`, `zero-hardcoding`, `dashboard-pattern`, `search-detail-pattern`
**CAHIER DES CHARGES** : `LarcCompta/CAHIER_DES_CHARGES.md`

Ce skill définit les règles métier de la gestion des frais de scolarité : le modèle de données
(parent-based), le calcul du statut, la propagation parent→enfant, la projection de trésorerie,
les alertes et les exports.

## 1. Fonction

### Type : Système Fermé

**Entrée** : Élèves (`larcauth_student`), Parents payeurs (`larcauth_parent.is_payer=TRUE`),
Barèmes (`compta_fee_level`), Paiements (`compta_payment`)
**Sortie** : Statut de chaque parent et enfant, Dashboard avec projection, Alertes
**Traitement** : Barème × Élève → `compta_student_fee` → Balance parent (`compta_parent_balance`) → Statut → Propagation enfant → Dashboard

## 2. Contraintes

### Sous-système SF — Modèle de Données

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| SF1 | **Paiement lié au parent** | `compta_payment.student_id` | `compta_payment.parent_id` — un virement = un parent | 🔴 P0 |
| SF2 | **Balance unique par parent** | Calculer le statut à la volée | `compta_parent_balance` (1 ligne par parent/an) — lu en 1 requête | 🔴 P0 |
| SF3 | **Barème par niveau** | Prix unique par programme | `compta_fee_level` : chaque niveau (PEI-1, MYP-3, DP-2) a son propre tarif | 🔴 P0 |
| SF4 | **Frais par élève** | Modifier le barème pour un cas particulier | `compta_student_fee` : copie du barème, modifiable individuellement | 🟡 P1 |
| SF5 | **Historique tracé** | Écraser sans trace | `change_history` (JSONB) : chaque changement daté et horodaté | 🔴 P0 |
| SF6 | **Preuves attachées** | Paiement sans justificatif | `compta_payment.file_url` + `cloud_url` : scan, photo, PDF | 🟡 P1 |

### Sous-système S1 — Algorithme de Statut

| # | Règle | Formule | Gravité |
|---|---|---|---|
| S1a | **Total dû** | `total_due = Σ compta_student_fee.annual_fee` | 🔴 P0 |
| S1b | **Total payé** | `total_paid = Σ compta_payment.amount` | 🔴 P0 |
| S1c | **Inscription prioritaire** | Milestone `type='inscription'` non soldé + date dépassée → `en_retard` | 🔴 P0 |
| S1d | **Attendu mensuel** | `attendu = total_due × %_echeancier` OU `Σ milestones` si personnalisé | 🔴 P0 |
| S1e | **Statut** | `paid ≥ total_due` → `solde` / `paid ≥ attendu` → `en_cours` / sinon → `en_retard` | 🔴 P0 |
| S1f | **Propagation** | Parent X → tous ses enfants sont X | 🔴 P0 |
| S1g | **Override** | Comptable peut forcer le statut → `status_override=TRUE` + badge ✎ | 🟡 P1 |

3 états = 3 couleurs de bordure : En retard (ROUGE) · En cours (VERT) · Soldé (BLEU)

### Sous-système S2 — Dashboard & Projection

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S2a | **Barre de santé** | Pas d'indicateur global | Jauge % encaissé + détail par programme | 🔴 P0 |
| S2b | **Deux courbes** | Courbe théorique unique | Standard (pointillés) + Ajustée (pleine, hors milestones perso) | 🔴 P0 |
| S2c | **Top 10 impayés** | Pas de tri | 10 plus gros soldes : parent, enfants, restant, dernier paiement | 🟡 P1 |
| S2d | **Alerte proactive** | Gestionnaire doit penser à vérifier | Badge rouge sur bouton Rappels si `en_retard ≥ seuil` + `restant > seuil_montant` | 🔴 P0 |
| S2e | **Export** | Pas de rapport | `[▾ Exporter]` → Impayés / Bilan annuel / Relevé individuel (Word) | 🟡 P1 |

### Sous-système S3 — Vignettes Élèves

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S3a | **Bordure colorée** | Toutes identiques | `set_payment_status(status)` : 2px ROUGE/VERT/BLEU | 🔴 P0 |
| S3b | **Texte statut** | Pas de label | `_status_label` : "En retard"/"En cours"/"Soldé" couleur bordure | 🔴 P0 |
| S3c | **Fond uniforme** | Fond différent par statut | `background: ds.p.surface` pour TOUS. Bordure seule change. | 🔴 P0 |
| S3d | **Badges cachés** | Afficher D/M/P/E | `_badges_row` masqué | 🟡 P1 |

### Sous-système S4 — Dossier Parent

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S4a | **Lecture balance** | Requêtes multiples | 1 `SELECT FROM compta_parent_balance` | 🔴 P0 |
| S4b | **Enfants + frais** | Sans montant | Niveau, classe, `annual_fee` par enfant | 🔴 P0 |
| S4c | **Paiements + preuves** | Sans justificatif | Date, montant, mode, référence, `file_url` cliquable | 🔴 P0 |
| S4d | **Historique visible** | Changements invisibles | `change_history` en timeline | 🟡 P1 |
| S4e | **Override** | Statut figé | Combo `en_cours`/`solde`/`en_retard`/`exonere` | 🔴 P0 |

### Sous-système S5 — Recouvrement

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S5a | **Liste actionnable** | Liste statique | Tri par montant, ancienneté, programme. Filtres par seuil. | 🔴 P0 |
| S5b | **Action groupée** | Un par un | Sélection multiple → rappel groupé aux X parents | 🟡 P1 |
| S5c | **Suivi efficacité** | Sans suivi | Colonne Résultat : `payé depuis` / `sans effet` | 🟡 P1 |

## 3. Code

### Lecture de la balance

```python
def get_parent_status(parent_id: int) -> dict:
    cur.execute("""
        SELECT total_due, total_paid, remaining, status, status_override, change_history
        FROM compta_parent_balance
        WHERE parent_id = %s AND academic_year = '2026-2027'
    """, (parent_id,))
    row = cur.fetchone()
    if not row:
        return {"status": "en_retard", "total_due": 0, "total_paid": 0, "remaining": 0}
    return {"total_due": row[0], "total_paid": row[1], "remaining": row[2],
            "status": row[3], "status_override": row[4], "change_history": row[5]}
```

### Mise à jour de la balance (après chaque paiement)

```python
def sync_balance(parent_id: int):
    # 1. Mettre à jour compta_parent_balance
    cur.execute("""
        INSERT INTO compta_parent_balance
            (parent_id, academic_year, total_due, total_paid, remaining, status, change_history)
        VALUES (%s, '2026-2027', %s, %s, %s, %s, %s)
        ON CONFLICT (parent_id, academic_year) DO UPDATE SET
            total_due = EXCLUDED.total_due, total_paid = EXCLUDED.total_paid,
            remaining = EXCLUDED.remaining, status = EXCLUDED.status,
            change_history = compta_parent_balance.change_history || EXCLUDED.change_history::jsonb,
            updated_at = NOW()
    """, (parent_id, total_due, total_paid, remaining, status,
          json.dumps([{"at": str(date.today()), "what": "paiement",
                       "new_status": status, "du": total_due, "paid": total_paid}])))
    # 2. Propager aux enfants
    cur.execute("""
        UPDATE larcauth_student SET statut_scolarite = %s
        WHERE aecuser_ptr_id IN (
            SELECT sp.student_id FROM larcauth_student_parent sp WHERE sp.parent_id = %s
        )
    """, (status, parent_id))
```

### Alerte proactive

```python
cur.execute("""
    SELECT COUNT(*) FROM compta_parent_balance
    WHERE status = 'en_retard' AND remaining > %s AND academic_year = '2026-2027'
""", (alert_min_amount,))
if cur.fetchone()[0] >= alert_threshold:
    self._nav_buttons['rappels'].setText(f"📅 Rappels ⚠ {count}")
```

## 4. Exemples

### ❌ Avant — Paiement lié à l'élève (erreur)

```python
# Un parent a 3 enfants, fait un virement de 3M
cur.execute("INSERT INTO compta_payment (student_id, amount) VALUES (%s, %s)", (student_1, 3000000))
# → Problème : le système ne sait pas que ce paiement couvre aussi student_2 et student_3
# → Chaque enfant semble avoir 0 ou 3M, jamais la réalité
```

### ✅ Après — Paiement lié au parent (correct)

```python
# Un parent a 3 enfants, fait un virement de 3M
cur.execute("INSERT INTO compta_payment (parent_id, amount) VALUES (%s, %s)", (parent_id, 3000000))
# → sync_balance(parent_id) recalcule tout
# → Les 3 enfants héritent du statut parent automatiquement
```

### ❌ Avant — Calcul du statut à la volée

```python
# Dans chaque vue : dashboard, parents_list, class_panel, reminders...
cur.execute("""SELECT COALESCE(SUM(amount),0) FROM compta_payment WHERE parent_id IN
    (SELECT parent_id FROM larcauth_student_parent WHERE student_id IN
     (SELECT aecuser_ptr_id FROM larcauth_student WHERE s_classroom_id = %s))""", (class_id,))
# → 4 requêtes imbriquées, 3 secondes, répétées dans chaque vue
```

### ✅ Après — Balance pré-calculée

```python
# Une seule requête, partout
cur.execute("SELECT total_due, total_paid, remaining, status FROM compta_parent_balance WHERE parent_id = %s", (pid,))
# → Instantané. Les 4 vues utilisent la même source.
```

## 5. Step by Step

| Ordre | Action | Table |
|---|---|---|
| 1 | Configurer les barèmes par niveau | `compta_fee_level` |
| 2 | Créer les frais par élève (copie du barème) | `compta_student_fee` |
| 3 | Créer les milestones d'inscription pour chaque parent | `compta_parent_milestone` |
| 4 | Peupler les balances (total_due, remaining, status) | `compta_parent_balance` |
| 5 | Marquer les parents avec milestones → `has_custom_schedule=TRUE` | `compta_parent_balance` |
| 6 | À chaque paiement → `sync_balance(parent_id)` | `compta_parent_balance` |
| 7 | Lire le statut via `get_parent_status(parent_id)` | `compta_parent_balance` |

## 6. Checklist

- [ ] SF1 : `compta_payment.parent_id` utilisé (jamais `student_id`)
- [ ] SF2 : `compta_parent_balance` existe et est lu en 1 SELECT
- [ ] SF5 : `change_history` enrichi à chaque modification
- [ ] S1a-S1e : Algorithme de statut correct (inscription prioritaire)
- [ ] S1f : Propagation parent→enfant via `larcauth_student.statut_scolarite`
- [ ] S1g : Combo override statut fonctionnel
- [ ] S2a : Barre de santé visible dans le dashboard
- [ ] S2b : Deux courbes de projection (standard + ajustée)
- [ ] S2d : Badge d'alerte sur le bouton Rappels
- [ ] S2e : Bouton Exporter fonctionnel (3 formats Word)
- [ ] S3a-S3c : Vignettes avec bordure colorée + texte + fond uniforme
- [ ] S4a : Dossier parent lit `compta_parent_balance` directement
- [ ] S5a : Liste impayés triable et filtrable

## 7. Références croisées

- **[design-tokens](../design-tokens/SKILL.md)** — ds.space_*, ds.p.*, ds.font_*
- **[color-rules](../color-rules/SKILL.md)** — D1 (couleur explicite), D6/D7 (restyle)
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — R1-R17, zéro pixel littéral
- **[dashboard-pattern](../dashboard-pattern/SKILL.md)** — DP1-DP8, KPI cards, charts
- **[search-detail-pattern](../search-detail-pattern/SKILL.md)** — Master-Detail
- **[card-grid-pattern](../card-grid-pattern/SKILL.md)** — Grille vignettes responsive
- **[graphify](../graphify/SKILL.md)** — Graphe de connaissances
- **[CAHIER_DES_CHARGES.md](../../../LarcCompta/CAHIER_DES_CHARGES.md)** — Spécification détaillée
