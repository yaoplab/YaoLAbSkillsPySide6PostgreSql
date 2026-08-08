---
skill: scolarite-finance
version: "1.0"
priority: P0
category: metier
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

Ce skill définit les **règles métier** de la gestion des frais de scolarité. Il couvre :
le modèle de données, le calcul du statut parent, la propagation parent→enfant,
la projection de trésorerie, les alertes et les exports.

## 1. Fonction Principale

### Type : Système Fermé

**Entrée** : Élèves (larcauth_student), Parents payeurs (larcauth_parent.is_payer=TRUE),
Barèmes (compta_fee_level), Paiements (compta_payment)
**Sortie** : Statut de chaque parent et enfant, Dashboard avec projection, Alertes
**Traitement** : Barème × Élève → Frais → Balance parent → Statut → Propagation enfant → Dashboard

---

## 2. Contraintes Fondamentales — Modèle de Données

### Sous-système SF — Structure Financière

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| SF1 | **Paiement lié au parent** | `compta_payment.student_id` | `compta_payment.parent_id` — un virement = un parent | 🔴 P0 |
| SF2 | **Balance unique par parent** | Calculer le statut à la volée dans chaque vue | `compta_parent_balance` (1 ligne par parent/an) — lu en 1 requête | 🔴 P0 |
| SF3 | **Barème par niveau** | Prix unique par programme | `compta_fee_level` : chaque niveau (PEI-1, MYP-3, DP-2) a son propre tarif | 🔴 P0 |
| SF4 | **Frais par élève** | Modifier le barème global pour un cas particulier | `compta_student_fee` : copie du barème, modifiable individuellement (bourse, réduction) | 🟡 P1 |
| SF5 | **Historique tracé** | Écraser l'ancien statut sans trace | `change_history` (JSONB) dans `compta_parent_balance` : chaque changement est daté et horodaté | 🔴 P0 |
| SF6 | **Preuves attachées** | Paiement sans justificatif | `compta_payment.file_url` + `cloud_url` : scan, photo, PDF du reçu | 🟡 P1 |

---

## 3. Contraintes Fondamentales — Calcul du Statut

### Sous-système S1 — Algorithme de Statut

| # | Règle | Formule | Gravité |
|---|---|---|---|
| S1a | **Total dû** | `total_due = Σ compta_student_fee.annual_fee` pour tous les enfants du parent | 🔴 P0 |
| S1b | **Total payé** | `total_paid = Σ compta_payment.amount` pour le parent | 🔴 P0 |
| S1c | **Inscription prioritaire** | Si milestone `type='inscription'` non soldé ET date dépassée → `en_retard` (même si échéances mensuelles OK) | 🔴 P0 |
| S1d | **Attendu mensuel** | `attendu = total_due × %_echeancier(mois_courant)` OU somme des `milestone` si personnalisé | 🔴 P0 |
| S1e | **Statut** | `paid ≥ total_due` → `solde` / `paid ≥ attendu` → `en_cours` / sinon → `en_retard` | 🔴 P0 |
| S1f | **Propagation** | Parent en retard → TOUS ses enfants en retard. Parent soldé → tous ses enfants soldés. | 🔴 P0 |
| S1g | **Override comptable** | Le comptable peut forcer le statut → `status_override=TRUE` + badge ✎ | 🟡 P1 |

### 3 états seulement

```
En retard — attendu non atteint → bordure ROUGE
En cours  — attendu atteint mais pas tout → bordure VERTE
Soldé     — tout payé → bordure BLEUE
```

---

## 4. Contraintes Fondamentales — Dashboard & Projection

### Sous-système S2 — Vue Gestionnaire

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S2a | **Barre de santé** | Dashboard sans indicateur global | Jauge horizontale colorée : `% encaissé` global + par programme (Collège, Lycée, Primaire) | 🔴 P0 |
| S2b | **Deux courbes de projection** | Une seule courbe théorique | Courbe standard (pointillés) + Courbe ajustée (pleine, exclut les milestones personnalisés) | 🔴 P0 |
| S2c | **Top 10 impayés** | Liste sans tri | Tableau des 10 plus gros soldes : parent, enfants, restant, dernier paiement | 🟡 P1 |
| S2d | **Alerte proactive** | Le gestionnaire doit penser à vérifier | Badge rouge sur le bouton « Rappels » si `nb_en_retard ≥ seuil` ET `restant > seuil_montant` | 🔴 P0 |
| S2e | **Export** | Pas de rapport pour la direction | Bouton `[▾ Exporter]` → 3 formats Word : État des impayés, Bilan annuel, Relevé individuel | 🟡 P1 |

---

## 5. Contraintes Fondamentales — Vignettes Élèves

### Sous-système S3 — Affichage Classe

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S3a | **Bordure colorée** | Toutes les vignettes identiques | `set_payment_status(status)` : bordure 2px ROUGE/VERTE/BLEUE selon statut hérité | 🔴 P0 |
| S3b | **Texte du statut** | Pas de label | `_status_label` en bas de la vignette : "En retard" / "En cours" / "Soldé" dans la couleur de la bordure | 🔴 P0 |
| S3c | **Fond uniforme** | Fond coloré différent par statut | `background: ds.p.surface` pour TOUS les statuts. Seule la bordure change. | 🔴 P0 |
| S3d | **Badges cachés** | Afficher D/M/P/E en vue compta | Les 4 badges `_badges_row` sont masqués. Inutiles en compta. | 🟡 P1 |

---

## 6. Contraintes Fondamentales — Parents (Master-Detail)

### Sous-système S4 — Dossier Parent

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S4a | **Lecture balance** | Requêtes multiples pour le statut | `SELECT FROM compta_parent_balance WHERE parent_id = ?` — 1 requête | 🔴 P0 |
| S4b | **Liste des enfants** | Enfants sans frais | Chaque enfant affiche son niveau, sa classe et son `annual_fee` | 🔴 P0 |
| S4c | **Chronologie des paiements** | Paiements sans preuve | Chaque paiement affiche date, montant, mode, référence, ET `file_url` cliquable | 🔴 P0 |
| S4d | **Historique visible** | Changements invisibles | `change_history` affiché en timeline dans le dossier parent | 🟡 P1 |
| S4e | **Override comptable** | Statut gravé dans le marbre | Combo pour forcer `en_cours`/`solde`/`en_retard`/`exonere` | 🔴 P0 |

---

## 7. Contraintes Fondamentales — Impayés & Rappels

### Sous-système S5 — Recouvrement

| # | Règle | ❌ Interdit | ✅ Obligatoire | Gravité |
|---|---|---|---|---|
| S5a | **Liste actionnable** | Liste statique | Tri par montant, ancienneté, programme. Filtres par seuil (>500K, >1M, >2M) | 🔴 P0 |
| S5b | **Action groupée** | Envoyer les rappels un par un | Sélection multiple → « Envoyer un rappel aux X parents sélectionnés » | 🟡 P1 |
| S5c | **Suivi efficacité** | Rappel sans suivi | Colonne "Résultat" : `payé depuis` / `sans effet`. Permet de mesurer l'impact. | 🟡 P1 |

---

## 8. Code Canonique — Lecture de la Balance

```python
# ✅ Pattern obligatoire — 1 requête, résultat immédiat
def get_parent_status(parent_id: int) -> dict:
    cur.execute("""
        SELECT total_due, total_paid, remaining, status, status_override,
               change_history
        FROM compta_parent_balance
        WHERE parent_id = %s AND academic_year = '2026-2027'
    """, (parent_id,))
    row = cur.fetchone()
    if not row:
        return {"status": "en_retard", "total_due": 0, "total_paid": 0, "remaining": 0}
    return {
        "total_due": row[0], "total_paid": row[1], "remaining": row[2],
        "status": row[3], "status_override": row[4], "change_history": row[5],
    }
```

## 9. Code Canonique — Mise à Jour de la Balance

```python
# ✅ Pattern obligatoire — déclenché après chaque paiement
def sync_balance(parent_id: int):
    cur.execute("""
        INSERT INTO compta_parent_balance
            (parent_id, academic_year, total_due, total_paid, remaining, status, change_history)
        VALUES (%s, '2026-2027', %s, %s, %s, %s, %s)
        ON CONFLICT (parent_id, academic_year) DO UPDATE SET
            total_due = EXCLUDED.total_due,
            total_paid = EXCLUDED.total_paid,
            remaining = EXCLUDED.remaining,
            status = EXCLUDED.status,
            change_history = compta_parent_balance.change_history || EXCLUDED.change_history::jsonb,
            updated_at = NOW()
    """, (parent_id, total_due, total_paid, remaining, status,
          json.dumps([{"at": str(date.today()), "what": "paiement",
                       "new_status": status, "du": total_due, "paid": total_paid}])))
    # Propager aux enfants
    cur.execute("""
        UPDATE larcauth_student SET statut_scolarite = %s
        WHERE aecuser_ptr_id IN (
            SELECT sp.student_id FROM larcauth_student_parent sp WHERE sp.parent_id = %s
        )
    """, (status, parent_id))
```

## 10. Step by Step — Création d'une Nouvelle Année Scolaire

| Ordre | Action | Table |
|---|---|---|
| 1 | Configurer les barèmes par niveau | `compta_fee_level` |
| 2 | Créer les frais par élève (copie du barème) | `compta_student_fee` |
| 3 | Créer les milestones d'inscription pour chaque parent | `compta_parent_milestone` |
| 4 | Peupler les balances (total_due, remaining, status) | `compta_parent_balance` |
| 5 | Marquer les parents avec milestones → `has_custom_schedule=TRUE` | `compta_parent_balance` |

## 11. Checklist

- [ ] SF1 : `compta_payment.parent_id` utilisé (jamais `student_id`)
- [ ] SF2 : `compta_parent_balance` existe et est lu en 1 requête
- [ ] SF5 : `change_history` enrichi à chaque modification
- [ ] S1a-S1e : Algorithme de statut correct (inscription prioritaire)
- [ ] S1f : Propagation parent→enfant via `larcauth_student.statut_scolarite`
- [ ] S2a : Barre de santé visible dans le dashboard
- [ ] S2b : Deux courbes de projection (standard + ajustée)
- [ ] S2d : Badge d'alerte sur le bouton Rappels
- [ ] S3a : Vignettes avec `set_payment_status()` (bordure colorée)
- [ ] S4a : Dossier parent lit `compta_parent_balance` directement
- [ ] S4e : Combo d'override statut fonctionnel

## 12. Références Croisées

- **[design-tokens](../design-tokens/SKILL.md)** — ds.space_*, ds.p.*, ds.font_*
- **[color-rules](../color-rules/SKILL.md)** — D1 (couleur explicite), D6/D7 (restyle)
- **[zero-hardcoding](../zero-hardcoding/SKILL.md)** — R1-R17, zéro pixel littéral
- **[dashboard-pattern](../dashboard-pattern/SKILL.md)** — DP1-DP8, KPI cards, charts
- **[search-detail-pattern](../search-detail-pattern/SKILL.md)** — Master-Detail (liste + dossier)
- **[card-grid-pattern](../card-grid-pattern/SKILL.md)** — Grille de vignettes responsive
- **[graphify](../graphify/SKILL.md)** — Graphe de connaissances
