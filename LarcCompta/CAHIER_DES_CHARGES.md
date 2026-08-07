# Cahier des charges — LarcCompta v2

## Principe fondateur

**Le parent est l'unité de compte.** Un parent paie pour tous ses enfants, quel que soit leur campus. Un paiement est lié à un parent, pas à un élève. Le statut de chaque enfant hérite du statut de son parent.

Deux entités comptables : le **parent payeur** (qui paie) et l**'enfant** (dont les frais sont dus). Le lien est simple : un parent payeur → N enfants → N frais. Un enfant peut avoir jusqu'à 2 payeurs. Le statut enfant hérite du meilleur statut de ses payeurs.

---

## 1. Modèle de données

### 1a. Barème par niveau — `compta_fee_level`

```sql
CREATE TABLE compta_fee_level (
    id              SERIAL PRIMARY KEY,
    level_id        INTEGER NOT NULL REFERENCES larcauth_level(id),
    academic_year   VARCHAR(9) NOT NULL,
    annual_fee      INTEGER NOT NULL,          -- montant annuel en FCFA
    monthly_amount  INTEGER,                    -- suggestion mensualité (annual_fee / 10)
    UNIQUE (level_id, academic_year)
);
```

Le tarif est lié au **niveau** (`larcauth_level`) pas au programme. MYP-1 peut coûter
différent de MYP-5. Chaque niveau a son propre montant.

### 1b. Frais par élève — `compta_student_fee`

```sql
CREATE TABLE compta_student_fee (
    id              SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES larcauth_aecuser(id),
    academic_year   VARCHAR(9) NOT NULL,
    level_id        INTEGER NOT NULL REFERENCES larcauth_level(id),
    annual_fee      INTEGER NOT NULL,          -- recopié du barème à la création
    payment_mode    VARCHAR(20) DEFAULT 'mensuel',  -- mensuel | trimestriel | annuel
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, academic_year)
);
```

Gabarit : un `compta_student_fee` est créé automatiquement pour chaque élève `enabled = TRUE`.
Le montant est copié du barème. Modifiable individuellement (bourse, réduction).

### 1c. Parent payeur — `larcauth_parent.is_payer`

```sql
ALTER TABLE larcauth_parent ADD COLUMN is_payer BOOLEAN DEFAULT FALSE;
```

- Le premier parent lié à un élève = `is_payer = TRUE` automatiquement
- Modifiable via la fiche parent (checkbox)
- Maximum 2 payeurs par famille
- Badge **P** (parent_valid) dans la vue secrétaire = au moins un parent `is_payer = TRUE`

### 1d. Paiement — `compta_payment`

```sql
-- Modifier la table existante
ALTER TABLE compta_payment DROP COLUMN student_id;
ALTER TABLE compta_payment ADD COLUMN parent_id INTEGER NOT NULL REFERENCES larcauth_aecuser(id);
```

Un paiement = un parent. Si le parent a 3 enfants qui totalisent 7.5M, il fait un virement de 2M — c'est un seul enregistrement. Pas de découpage artificiel par enfant.

### 1e. Document joint — `compta_payment_document`

```sql
CREATE TABLE compta_payment_document (
    id              SERIAL PRIMARY KEY,
    payment_id      INTEGER REFERENCES compta_payment(id),
    parent_id       INTEGER NOT NULL REFERENCES larcauth_aecuser(id),
    file_path       TEXT,
    title           VARCHAR(200),
    amount          INTEGER,
    document_date   DATE DEFAULT CURRENT_DATE,
    created_by      INTEGER REFERENCES larcauth_aecuser(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    notes           TEXT
);
```

Pour les documents sans paiement associé (devis, attestation, facture pro forma), `payment_id` est NULL. Le document est lié au parent.

### 1f. Rappel — `compta_reminder`

```sql
-- Modifier la table existante
ALTER TABLE compta_reminder DROP COLUMN student_id;
ALTER TABLE compta_reminder ADD COLUMN parent_id INTEGER NOT NULL REFERENCES larcauth_aecuser(id);
```

Un rappel est envoyé au parent pour l'ensemble de ses enfants.

---

## 2. Calcul du statut

### Par parent payeur

```python
total_dû_parent    = Σ(compta_student_fee.annual_fee de chaque enfant)
total_payé_parent  = Σ(compta_payment.amount du parent)
solde_parent       = total_payé_parent - total_dû_parent

STATUT_PARENT = {
    solde >= 0:           "solde",    # vert
    payé > 0 et solde < 0: "normal",  # orange (en cours)
    payé == 0:             "retard",  # rouge
}
```

### Par enfant (hérité du parent)

```
enfant.statut = meilleur_statut(statut_parent1, statut_parent2)
```

Si aucun parent payeur lié → pas d'enfant dans la vue compta. Le badge P sera rouge côté secrétaire.

---

## 3. UI — Vues

### 3a. Sidebar final

```
┌─────────────────────┐
│ 👤 Utilisateur      │
│ Comptabilité        │
│ ─────────────────── │
│ 🏫 Collège          │  ← SidebarWidget (programmes + classes)
│   PEI               │
│   MYP               │
│ 🎓 Lycée            │
│   DP                │
│ ─────────────────── │
│ 📊 Tableau de bord   │  ← NavButton (existant)
│ 👤 Parents           │  ← refactoré : statut parent
│ 🏫 Élèves             │  ← refactoré : statut hérité
│ 📁 Dossiers           │  ← NOUVEAU
│ 💰 Paiements          │  ← refactoré : lié au parent
│ 📅 Rappels            │  ← refactoré : lié au parent
│ ⚙ Configuration       │  ← NOUVEAU
└─────────────────────┘
```

### 3b. Dashboard (existant, à ajuster)

KPIs et graphiques basés sur les parents payeurs, pas les élèves.

### 3c. Parents (existant, à refactorer)

Liste de tous les parents avec `is_payer = TRUE`. Chaque ligne :
- Nom parent, nombre d'enfants, total dû, total payé, solde, statut (badge coloré), progression bar

### 3d. Élèves (existant, à refactorer)

Liste de tous les élèves avec leur statut hérité. Tri par statut (retard en premier).

### 3e. Dossiers parent — NOUVEAU

Recherche un parent → ouvre son dossier comptable :
- En-tête : nom parent, enfants, total dû, total payé, solde
- Timeline chronologique : paiements + documents
- Chaque entrée : date, type, montant, titre, fichier joint, note
- Bouton "Ajouter un document" → upload (scan reçu, preuve virement)
- Bouton "Enregistrer un paiement" → dialogue rapide

### 3f. Paiements (existant, à refactorer)

- Liste de tous les paiements (date, parent, montant, mode, référence)
- Formulaire : **recherche parent** (plus élève), montant, date, mode

### 3g. Rappels (existant, à refactorer)

- Liste des parents en retard (solde < 0)
- Envoi rappel au parent pour l'ensemble de ses enfants
- Message pré-rempli avec détail par enfant

### 3h. Configuration — NOUVEAU

- Tableau éditable : Niveau | Programme | Montant annuel | Mensualité suggérée
- Double-clic pour modifier un montant
- Bouton "Appliquer à tout le programme" pour initialisation rapide

### 3i. Vignettes classe (existant, à ajuster)

- Classe → grille de `StudentCard`
- Bordure et badge hérités du parent payeur
- 3 couleurs : vert (soldé), orange (en cours), rouge (en retard)

---

## 4. Plan d'implémentation

| Phase | Livrable |
|---|---|
| **1. SQL** | `compta_fee_level`, `compta_student_fee`, `compta_payment_document`. Modifier `compta_payment` (parent_id), `compta_reminder` (parent_id). Ajouter `larcauth_parent.is_payer`. Seed des barèmes par niveau. |
| **2. Configuration** | `fee_config.py` — UI tableau éditable des barèmes. |
| **3. Paiements refactor** | Formulaire de paiement : recherche parent (plus élève). Liste des paiements : groupés par parent. |
| **4. Dossiers parent** | `parent_dossier.py` — recherche parent → timeline documents + upload. |
| **5. Calcul statut** | Vue `ClassPaymentPanel` → statut hérité du parent. `StudentsList` → idem. `ParentsList` → statut parent. |
| **6. Rappels** | Adaptés au parent (message récapitulatif par enfant). |
| **7. Dashboard** | KPIs basés sur les parents (pas les élèves). |
| **8. Lint + tests** | Tous les linters verts. |

---

## 5. Règles métier

1. **Un paiement = un parent.** Jamais lié directement à un élève.
2. **Statut enfant hérité.** Si parent soldé → enfant soldé.
3. **Pas de payeur = pas dans la compta.** Un élève sans parent payeur n'apparaît pas dans les vues comptables.
4. **Badge P = un payeur minimum.** Côté secrétaire, le dossier parent n'est valide que si `is_payer = TRUE`.
5. **1 payeur par défaut, 2 max.** Le premier parent lié est automatiquement payeur. Modifiable.
6. **Barème par niveau.** Chaque niveau a son tarif. Modifiable dans l'UI Configuration.
7. **Frais par élève = copie du barème.** Modifiable individuellement (bourse).
8. **Documents au parent.** Reçus, factures et preuves sont attachés au dossier parent, pas à l'élève.
