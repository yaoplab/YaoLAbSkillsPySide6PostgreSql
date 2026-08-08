# Cahier des charges — LarcScolarité v3

## Vue d'ensemble

LarcScolarité est l'outil de suivi financier de l'établissement. Il permet au responsable
de **voir** l'état des comptes, **prévoir** les rentrées futures et **agir** sur les retards.
Tout est construit autour de `compta_parent_balance` — la balance comptable par parent.

### Écrans

```
┌─────────────────────┬──────────────────────────────────────────────────────┐
│ SIDEBAR             │ CONTENU                                              │
│                     │                                                      │
│ 🏫 Classes          │ [Selon sélection]                                    │
│   PEI · MYP · DP   │                                                      │
│ ─────────────────── │  → Programme : Dashboard filtré                      │
│ 📊 Vue d'ensemble   │  → Classe : Vignettes colorées                       │
│ 👤 Parents          │  → "Vue d'ensemble" : Dashboard global               │
│ ⚠ Impayés           │  → Parents : Master-Detail                           │
│ 📅 Rappels          │  → Impayés : Liste actionnable                       │
│ ⚙ Configuration    │  → Rappels : Suivi des relances                       │
└─────────────────────┴──────────────────────────────────────────────────────┘
```

---

## 1. Vue d'ensemble (Dashboard)

### 1a. Barre de santé

Une jauge horizontale en haut du dashboard :

```
████████████████████████████████████████████████░░░░░░░░  78% encaissé
      Collège 82%  │  Lycée 71%  │  Primaire 89%
```

Lecture immédiate : 78% de l'argent attendu est rentré. Le gestionnaire sait en 1 seconde.

### 1b. KPIs

4 indicateurs clés au format M3 :

| KPI | Valeur exemple |
|---|---|
| **Encaissé** | 742 M FCFA |
| **Restant** | 258 M FCFA |
| **En retard** | 42 parents (84 élèves) |
| **Solde** | 189 parents (312 élèves) |

### 1c. Projection de fin d'année

Un graphique simple : courbe attendue vs courbe réelle.

```
100% │                                    ● attendu
 80% │              ●───────● réél       /
 60% │         ●───/                     /
 40% │    ●──/                          /
 20% │ ●─/                             /
  0% └─────────────────────────────────
     Sept Oct Nov Déc Jan Fév Mar Avr Mai Juin
```

Le gestionnaire voit si la courbe réelle rattrape l'attendue ou si elle décroche.

### 1d. Top 10 des impayés

Un petit tableau en bas du dashboard avec les 10 plus gros soldes :

| Parent | Enfants | Restant | Dernier paiement |
|---|---|---|---|
| Konan Paul | 2 | 4 200 000 | 15/09/2026 |
| ... | ... | ... | ... |

---

## 2. Master-Detail Parents

Déjà implémenté. Sélection d'un parent → dossier complet :

- **En-tête** : nom, contact, statut (avec badge ✎ si overridden)
- **Enfants** : liste avec frais annuels
- **Paiements** : chronologie avec preuves (file_url cliquable)
- **Résumé** : total dû, payé, restant, attendu, barre de progression
- **Statut modifiable** : combo si le gestionnaire veut forcer
- **Historique** : `change_history` visible (ligne du temps)

---

## 3. Impayés (nouvelle page)

Remplace "Élèves" et centralise l'action.

### 3a. Liste triable

Tableau triable par : nom, montant restant, ancienneté du dernier paiement, nombre d'enfants.

### 3b. Filtres

- Par programme (PEI, DP, etc.)
- Par seuil (> 500K, > 1M, > 2M restants)
- Par ancienneté (pas payé depuis 1 mois, 3 mois, 6 mois)

### 3c. Action groupée

Sélection multiple → « Envoyer un rappel aux X parents sélectionnés »

---

## 4. Rappels (refondu)

### 4a. Campagne de rappels

Le gestionnaire peut créer une campagne :

1. Il sélectionne une cible (ex : tous les parents en retard > 1M)
2. Il choisit le canal (email, SMS, WhatsApp, courrier)
3. Le système génère un message personnalisé par parent
4. Envoi groupé

### 4b. Suivi des rappels

Tableau : date d'envoi, parent, canal, montant dû à ce moment, résultat.

Deux colonnes : **Statut** (envoyé, échec, lu) et **Résultat** (payé depuis, sans effet).

Cela permet au gestionnaire de savoir quels rappels ont été efficaces.

---

## 5. Échéancier et inscriptions

### 5a. Inscription

Chaque parent a un milestone `type='inscription'` (frais d'inscription, montant fixe par élève). Ce milestone est créé en début d'année. Il est prioritaire : si l'inscription n'est pas payée, le statut est **en retard**, même si les échéances mensuelles sont à jour.

### 5b. Échéances mensuelles

L'échéancier global (`compta_payment_schedule`) définit le % attendu à la fin de chaque mois. Le système compare `total_paid` au `total_due × %_attendu`.

### 5c. Échéances personnalisées

Un parent peut négocier un plan de paiement différent → `compta_parent_milestone`. Les milestones personnalisés remplacent l'échéancier global pour ce parent.

---

## 6. Flux de travail type

### Septembre — Début d'année

1. Le comptable configure les barèmes (`fee_config.py`)
2. Le système crée les milestones d'inscription pour tous les parents
3. Le système crée les `compta_student_fee` pour tous les élèves

### Chaque mois

1. Le comptable ouvre la **Vue d'ensemble** → voit la jauge
2. Si la courbe réelle décroche → il ouvre **Impayés**
3. Il sélectionne les parents en retard → **Rappels** groupés
4. Les parents se présentent → il enregistre les paiements depuis le dossier parent

### Fin d'année — Clôture

1. Le comptable vérifie que tous les statuts sont soldés
2. Il force manuellement les statuts des exonérés
3. Il exporte le bilan annuel

---

## 7. Ce qui change par rapport à aujourd'hui

| Écran | État actuel | Cible |
|---|---|---|
| Dashboard | KPIs + donut + bar + table | + Barre de santé + Projection + Top 10 |
| Parents | Master-Detail | OK (reste le file_url à rendre cliquable dans l'OS) |
| Impayés | N'existe pas | Nouvelle page (liste actionnable + filtres) |
| Rappels | Liste plate | Campagnes groupées + suivi résultat |
| Configuration | Barèmes + échéancier | OK |
| Élèves | Supprimé | Intégré dans les vignettes classe |
| Paiements | Supprimé | Intégré dans le dossier parent |

---

## 8. Fichiers à créer / modifier

| Fichier | Action |
|---|---|
| `dashboard.py` | Ajouter barre santé, projection, top 10 |
| `impayes.py` | **NOUVEAU** — liste actionnable + filtres |
| `reminders.py` | Refonte : campagnes groupées + suivi |
| `main_window.py` | Ajouter "Impayés" dans NAV_ITEMS |
| `parents_list.py` | OK (peaufinage file_url) |

## 9. Priorité

1. **Impayés** — le plus urgent, remplace "Élèves" et "Paiements"
2. **Barre de santé + projection** — différencie visuellement
3. **Rappels groupés** — automatise les relances
4. **Suivi des rappels** — mesure l'efficacité
