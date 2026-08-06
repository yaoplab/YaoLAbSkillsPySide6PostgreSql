---
skill: graphify
version: "1.0"
priority: P0
category: infra
depends_on: []
applies_to: [LarcCommon, LarcSuperviseur, LarcSecretaire, LarcProf, LarcHub, LarcDesign, LarcCloudSync, LarcSupMobile]
linters: []
reviewers: [infra-reviewer]
subsystems: [G]
---

# Skill: Graphify — Graphe de Connaissances du Codebase

## 0. Contexte

**Projet** : Larc (tous les modules du monorepo)
**Outil** : [Graphify](https://github.com/Graphify-Labs/graphify) (`graphifyy` sur PyPI)
**Utilisateurs** : Agents IA et développeurs — compréhension globale sans lire tout le code
**Dépendances** : Aucune (fondation autonome)

Graphify transforme l'intégralité du codebase (Python, SQL, Markdown, configs)
en un **graphe de connaissances interrogeable**. C'est le "cerveau Obsidian" du projet :
au lieu de lire des milliers de fichiers, l'agent parcourt le graphe.

## 1. Fonction principale

**Entrée** : Le codebase complet (`C:\projets\`)
**Traitement** : Parsing AST via tree-sitter (~40 langages) + extraction sémantique
**Sortie** : `graphify-out/` contenant :
- `graph.json` — graphe JSON interrogeable (nœuds + arêtes typées)
- `graph.html` — visualisation interactive navigateur
- `GRAPH_REPORT.md` — synthèse des points clés (god nodes, communautés, liens cross-file)

### Types d'arêtes
| Arête | Méthode | Confiance |
|---|---|---|
| `calls` | AST tree-sitter | EXTRACTED |
| `imports` | AST tree-sitter | EXTRACTED |
| `inherits` | AST tree-sitter | EXTRACTED |
| `mixes_in` | AST tree-sitter | EXTRACTED |
| Relations sémantiques | LLM (selon config) | INFERRED |

### Fonctionnalités clés
- **God nodes** — les concepts les plus connectés, ce par quoi tout passe
- **Community detection** — clustering Leiden qui découpe le graphe en sous-systèmes
- **Requêtage** : `graphify query "<question>"`, `graphify path A B`, `graphify explain "Concept"`
- **Exports** : HTML interactif, vault Obsidian, SVG, GraphML (Gephi/yEd), Neo4j, wiki

## 2. Contraintes fondamentales

| # | Règle | Anti-pattern | Correct | Sévérité |
|---|---|---|---|---|
| G1 | Régénérer le graphe après chaque changement structurel | Modifier le code sans regénérer → agent sur vue obsolète | `graphify extract . --code-only --force && graphify cluster-only .` | P0 |
| G2 | Consulter le graphe AVANT toute tâche ≥3 fichiers | Lire les fichiers un par un sans vue d'ensemble | `graphify query "<question>"` puis identifier god nodes et communautés | P0 |
| G3 | Les arêtes EXTRACTED sont factuelles, les INFERRED sont des suggestions | Traiter les arêtes INFERRED comme des faits sans vérification | Vérifier dans le code source si doute sur une arête INFERRED | P1 |
| G4 | Export Obsidian pour navigation humaine | Documentation statique qui se périme | `graphify . --obsidian` → vault navigable, liens auto-générés | P1 |
| G5 | Git hook post-commit pour mise à jour automatique | Commit sans mise à jour → divergence graphe/code | `graphify hook install` + `GRAPH_REPORT.md` versionné | P2 |

## 3. Code complet

### Installation (30 secondes)
```bash
uv tool install graphifyy
graphify install
```

### Configuration `.graphify.yaml`
```yaml
# À la racine du projet
exclude:
  - ".venv/**"
  - ".git/**"
  - "**/__pycache__/**"
  - "*.pyc"
  - "node_modules/**"
  - ".aider*"
  - "**/cache/**"
  - "*.db-shm"
  - "*.db-wal"

include:
  - "**.py"
  - "**.md"
  - "**.sql"
  - "**.json"
  - "**.toml"
  - "**.yaml"
  - "**.ini"
  - "**.dart"

project_name: "Larc"
output_dir: "graphify-out"
```

### Génération du graphe
```bash
cd C:\projets
graphify extract . --code-only --force  # AST uniquement (pas de LLM)
graphify cluster-only .                  # Clustering + rapport + HTML
```

### Requêtage
```bash
graphify query "Comment LarcProf se connecte a la base ?"
graphify path LarcCommon LarcSuperviseur
graphify explain "ThemeManager"
graphify god-nodes --top 15
```

## 4. Exemples

### ❌ Avant — navigation sans graphe
```
Agent: lit main.py → lit login.py → lit database.py → lit session.py →
       lit auth.py → lit theme.py → 6 fichiers lus, 0 connexions comprises
Temps: ~3 minutes. Résultat: vue partielle, rate les dépendances indirectes.
```

### ✅ Après — navigation avec graphe
```
Agent: graphify query "Comment fonctionne l'authentification ?"
       → DataLoader(156) ↔ AuthManager(45) ↔ Session(38) ↔ ThemeManager(42)
       Agent: lit auth.py + session.py uniquement
Temps: ~30 secondes. Résultat: toutes les connexions comprises, 4 fichiers sautés.
```

### ❌ Avant — refactoring sans regénérer
```
Dev: refactore database.py (extrait en 2 fichiers)
Agent suivant: interroge le graphe → les chemins sont cassés, arêtes fantômes
→ confusion, perte de temps
```

### ✅ Après — refactoring avec regénération
```
Dev: refactore database.py
Dev: graphify extract . --code-only --force && graphify cluster-only .
Agent suivant: interroge le graphe → chemins à jour, nouveaux god nodes visibles
→ navigation fiable
```

## 5. Step by Step — mise en place

1. Installer graphify : `uv tool install graphifyy && graphify install`
2. Créer `.graphify.yaml` à la racine (recopier la section 3)
3. Premier build : `graphify extract . --code-only --force && graphify cluster-only .`
4. Vérifier : `graphify god-nodes --top 10` — DataLoader, safe_slot, log doivent apparaître
5. Ouvrir `graphify-out/graph.html` dans le navigateur — vérifier les communautés
6. Ajouter `graphify hook install` pour mise à jour automatique (optionnel)
7. Ajouter au CLAUDE.md la section Graphify (déjà fait)

## 6. Checklist

- [ ] Graphify installé (`uv tool install graphifyy && graphify install`)
- [ ] `.graphify.yaml` créé à la racine avec exclusions
- [ ] Graphe généré (`graphify extract . --code-only --force && graphify cluster-only .`)
- [ ] `graphify-out/graph.html` s'ouvre dans le navigateur
- [ ] God nodes identifiés et cohérents avec l'architecture
- [ ] Communautés vérifiées (pas d'orphelines)
- [ ] `graphify path LarcCommon LarcSuperviseur` fonctionnel
- [ ] Export Obsidian fonctionnel (optionnel)
- [ ] Git hook post-commit configuré (optionnel)
- [ ] `GRAPH_REPORT.md` versionné

## 7. Références croisées

- [[CLAUDE.md]] — conventions et architecture du projet
- [[open-design/AGENTS.md]] — instructions pour agents IA
- [[open-design/CONTEXT.md]] — contexte du projet
- Skills liés : [[database-operations]] (connexions), [[sync]] (synchro), [[toolkit-reference]] (widgets)
- Agent reviewer : [[open-design/agents/graphify-reviewer.md]]
