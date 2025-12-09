**AI50 — Multi-Agent Patrolling Simulation**

Simulation d'algorithmes de patrouille multi-agents sur grilles (interface Pygame + outils Streamlit).

**Résumé**:
- **But**: fournir un environnement expérimental pour comparer des stratégies de patrouille multi-agents (heuristique, fourmis/ACO, variantes) sur des cartes en grille, mesurer la couverture et l'idleness, et visualiser les statistiques.
- **Interface**: application principale en `pygame` (exécutable via `src/main.py`) et tableau de statistiques visualisable via `Streamlit` (`src/streamlit/stats.py`).

**Fonctionnalités principales**:
- **Algorithmes inclus**: `Heuristic`, `AntColony`, `AntColonyLecture` (implémentés dans `src/algorithm/`).
- **Gestion d'événements**: événements aléatoires ou scénarisés affectant l'idleness (voir `src/events/events.py`).
- **Chargement de cartes**: JSON + PNG via `src/maps/MapLoader.py` (cartes d'exemple dans `src/maps/`).
- **Instances prédéfinies**: gestion d'instances (positions initiales, paramètres) via `src/instances/instances.py` et `src/instances/instances.json`.
- **Export/visualisation des statistiques**: sauvegarde JSON et visualisation interactive avec `Streamlit` (`src/streamlit/saves/`).

**Organisation du dépôt**
- **`src/main.py`**: point d'entrée de l'application Pygame (UI principale).
- **`src/algorithm/`**: implémentations d'algorithmes et base abstraite `Algorithm`.
- **`src/maps/`**: cartes et `MapLoader` pour charger/sauver des cartes JSON/PNG.
- **`src/events/`**: simulation et gestion d'événements (apparition, effet sur idleness).
- **`src/instances/`**: gestionnaire d'instances et fichier `instances.json`.
- **`src/streamlit/`**: page Streamlit pour visualiser les statistiques sauvegardées.
- **`src/ui/`**: composants et configuration de l'interface utilisateur (`config.py` expose `sim_config`).

**Dépendances**
- Le fichier `requirements.txt` contient les dépendances principales :
	- `pygame`
	- `numpy`
	- `pandas`
	- `streamlit`
	- `plotly`

Installez-les (exemple venv Windows PowerShell) :

```powershell
python -m venv venv
; .\venv\Scripts\Activate.ps1
; pip install -r requirements.txt
```

**Exécution**
- Lancer l'interface Pygame (simulation interactive) :

```powershell
python src\main.py
```

- Ouvrir l'interface de statistiques Streamlit (visualiser les JSONs sauvegardés) :

```powershell
streamlit run src\streamlit\stats.py
```

**Configuration et personnalisation**
- Configuration globale : éditez `src/ui/config.py` ou modifiez `sim_config` dynamiquement depuis l'UI (map, algorithme par défaut, nombre d'agents, paramètres algorithmiques).
- Cartes : ajoutez des fichiers JSON dans `src/maps/` (format attendu par `MapLoader.load`, voir exemples `DUST2.json`, `Mirage.json`, `Inferno.json`).
- Instances : éditez `src/instances/instances.json` pour définir positions d'agents, paramètres d'idleness ou scénarios d'événements.

**Structure des algorithmes**
- `Algorithm` (base) fournit : grille, positions agents, grille d'idleness, gestionnaire d'événements, et métriques (couverture, idleness moyenne/max, travail par agent).
- `Heuristic` : partitionne l'espace en clusters et utilise un déplacement glouton vers les cellules à plus forte idleness.
- `AntColony` / `AntColonyLecture` : variantes ACO avec phéromones, évaporation et listes tabu.

**Sorties & Sauvegardes**
- Le simulateur produit des JSONs de statistiques utilisables par `src/streamlit/stats.py`. Par défaut, regardez le dossier `src/streamlit/saves/`.

**Conseils pour le développement**
- Le code est écrit en Python 3.x et utilise des types (annotations) pour faciliter la maintenance.
- Tests et validation : le dépôt ne contient pas de suite de tests automatisés; pour valider, lancez des simulations via `main.py` puis inspectez les fichiers JSON sauvegardés.