# Architecture Decision Records — TaskBoard

## ADR-001 — Architecture monolithique (et non microservices)

**Statut** : Adopté

**Contexte**
On veut un premier rendu rapide. L'équipe est petite, le périmètre initial (utilisateurs,
tâches, minuteur, dashboard temps réel, back-office) est cohérent et peut vivre dans un
seul déployable. Une architecture microservices ajouterait de la complexité
(orchestration, réseau interne, observabilité distribuée) sans bénéfice à ce stade.

**Décision**
Un seul backend Python (FastAPI) qui expose :
- une API REST (CRUD utilisateurs / tâches / affectations),
- un endpoint WebSocket (mises à jour temps réel : création, démarrage, fin, retard),
- le service des fichiers statiques du dashboard (écran TV) si besoin, ou un frontend
  séparé qui consomme l'API.

Le monolithe est découpé en **modules internes clairs** (routers, services, models) pour
pouvoir être scindé plus tard sans réécriture complète (voir ADR-003).

**Conséquences**
- Déploiement simple (un conteneur + une base Postgres).
- Un seul cycle de release au début.
- Point de vigilance : garder les modules découplés (pas de dépendances croisées
  implicites) pour permettre une extraction future en service séparé.

---

## ADR-002 — Stack technique : Python / FastAPI / PostgreSQL / WebSocket

**Statut** : Adopté

**Contexte**
Contrainte explicite : stack Python. Besoin de temps réel (timers, alertes) et d'une
base de données relationnelle robuste derrière.

**Décision**
- **FastAPI** : framework Python asynchrone, rapide à développer, documentation OpenAPI
  automatique (utile pour la future intégration avec d'autres apps / le kit Arduino).
- **PostgreSQL** : base relationnelle, fiable pour les relations User ↔ Task ↔ Assignment
  et l'historique/archive.
- **SQLAlchemy 2.0 (async) + Alembic** : ORM + migrations versionnées.
- **WebSocket natif de FastAPI** : diffusion des événements `task.created`,
  `task.started`, `task.completed`, `task.overdue` vers le dashboard TV et le back-office
  sans polling.
- **Pydantic** : validation des schémas d'entrée/sortie de l'API.

**Conséquences**
- Un seul langage (Python) sur tout le backend → onboarding plus rapide.
- FastAPI génère `/docs` (Swagger) automatiquement : utile le jour où une autre
  application (ou l'Arduino via une passerelle) doit consommer l'API.

---

## ADR-003 — API-first, pour permettre l'intégration future (autres apps, kit Arduino)

**Statut** : Adopté

**Contexte**
L'app est amenée à communiquer plus tard avec d'autres applications via API, et un kit
Arduino sera utilisé pour de l'automatisation (ex : déclencher une action physique
quand une tâche démarre/se termine, ou remonter un événement matériel qui crée/complète
une tâche).

**Décision**
- Toute action métier passe par l'API REST (pas de logique cachée uniquement dans le
  frontend). Le dashboard et le back-office sont de simples clients de cette API.
- Un **token API (clé service)** est prévu dès le départ pour les clients machine-to-
  machine (ex. passerelle Arduino), en plus de l'auth utilisateur (JWT) pour les humains.
- L'Arduino ne se connecte pas en direct au backend : on prévoit un **petit service
  passerelle** (script Python, ex. `pyserial` ou MQTT) qui traduit les événements
  série/MQTT de l'Arduino en appels HTTP vers l'API TaskBoard (`POST /tasks`,
  `PATCH /tasks/{id}/complete`, etc.). Ce sera un module séparé (`apps/arduino-bridge/`)
  ajouté en phase 2, sans toucher au cœur de l'API.
- Le WebSocket est aussi ouvert à des consommateurs externes (lecture seule) via un
  token, pour qu'une autre application puisse s'abonner aux événements sans repasser par
  du polling REST.

**Conséquences**
- Aucun changement de contrat requis quand l'Arduino ou une app tierce arrivera : ils
  consomment la même API que le dashboard.
- Prévoir dès le schéma de DB un champ `source` sur `Task` (`manuel`, `api`, `arduino`)
  pour tracer l'origine d'une tâche.

---

## ADR-004 — Notifications sonores côté client, pas côté serveur

**Statut** : Adopté

**Contexte**
Le dashboard tourne sur un écran TV. Le "son" est une expérience utilisateur locale à
cet écran.

**Décision**
Le backend ne fait qu'émettre des **événements WebSocket typés**
(`task.created`, `task.completed`, `task.overdue`). C'est le client (dashboard TV,
back-office) qui décide de jouer un son ou d'afficher un toast selon l'événement reçu.
Cela garde le backend simple et permet à chaque écran de configurer ses propres alertes.

**Conséquences**
- Le format des événements WebSocket doit être stable et documenté (voir
  `docs/CONCEPTION.md`).
