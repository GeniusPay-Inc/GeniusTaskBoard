# Conception — TaskBoard (v1, monolithe Python)

## 1. Périmètre (issu des échanges + notes manuscrites)

- **Personnel (Utilisateurs)** : créer, modifier, archiver (pas de suppression dure —
  on garde l'historique).
- **Tâches** : créer, affilier à une ou plusieurs personnes, avec un temps alloué
  (minutes) défini.
- **Interface de suivi (dashboard TV)** : afficher les tâches et les personnes
  affiliées, avec le temps restant en direct.
- **Back-office** : pilotage — création/gestion du personnel et des tâches
  (avec leurs timers), vue d'ensemble.
- **Moniteur / alertes** : quand une tâche est créée ou terminée, le moniteur
  (dashboard) déclenche une alerte visuelle + sonore.
- Interface **responsive**.
- Architecture pensée pour évoluer vers des échanges API avec d'autres applications
  et un kit **Arduino** (automatisation).

## 2. Modèle de données

```
Personnel (User)
- id: UUID (PK)
- nom: str
- prenom: str
- role: enum(admin, employe)
- statut: enum(actif, archive)
- created_at, updated_at

Task
- id: UUID (PK)
- titre: str
- description: str | null
- minutes_allouees: int              # temps confié pour la réalisation
- statut: enum(a_faire, en_cours, terminee, en_retard, archivee)
- source: enum(manuel, api, arduino) # d'où vient la tâche (ADR-003)
- date_debut: datetime | null
- date_fin_prevue: datetime | null   # calculée = date_debut + minutes_allouees
- date_fin_reelle: datetime | null
- created_at, updated_at

TaskAssignment (table pivot Task <-> Personnel)
- id: UUID (PK)
- task_id: FK -> Task
- user_id: FK -> Personnel
- assigned_at: datetime
```

## 3. API REST (v1)

Base : `/api/v1`

| Méthode | Route                          | Description                                   |
|---------|---------------------------------|------------------------------------------------|
| POST    | `/users`                        | Créer une personne du personnel                |
| GET     | `/users`                        | Lister le personnel (filtrable par statut)      |
| GET     | `/users/{id}`                   | Détail + tâches en cours                        |
| PATCH   | `/users/{id}`                   | Modifier                                        |
| POST    | `/users/{id}/archive`           | Archiver (au lieu d'un DELETE)                  |
| POST    | `/tasks`                        | Créer une tâche (avec `minutes_allouees`)       |
| GET     | `/tasks`                        | Lister (filtrable par statut / utilisateur)     |
| GET     | `/tasks/{id}`                   | Détail                                          |
| PATCH   | `/tasks/{id}`                   | Modifier                                        |
| POST    | `/tasks/{id}/assign`            | Affilier à un ou plusieurs `user_id`            |
| POST    | `/tasks/{id}/start`             | Démarrer (fixe `date_debut`, calcule l'échéance)|
| POST    | `/tasks/{id}/complete`          | Terminer (fixe `date_fin_reelle`)               |
| POST    | `/tasks/{id}/archive`           | Archiver                                        |
| GET     | `/dashboard`                    | Vue agrégée : tâches en cours + temps restant   |

Authentification : `X-API-Key` requis sur toutes les routes d'écriture (`POST`/`PATCH`),
partagée par le back-office et les futurs clients machine (passerelle Arduino / autres
apps). Un JWT par utilisateur (phase 2) viendra s'ajouter pour distinguer les personnes
qui pilotent le back-office.

## 4. Temps réel — WebSocket

Endpoint : `WS /ws?token=...`

Événements émis (JSON) :
```json
{ "type": "task.created",   "task": { ... } }
{ "type": "task.started",   "task": { ... } }
{ "type": "task.completed", "task": { ... } }
{ "type": "task.overdue",   "task": { ... } }
{ "type": "user.updated",   "user": { ... } }
```
Le dashboard TV s'abonne et déclenche toast + son selon le `type` reçu (ADR-004).
Le temps restant affiché est recalculé côté client à partir de `date_fin_prevue`
(pas besoin que le serveur pousse un événement chaque seconde).

## 5. Arborescence du dépôt

```
taskboard/
├── docs/
│   ├── ADR.md
│   └── CONCEPTION.md
├── app/
│   ├── main.py              # point d'entrée FastAPI
│   ├── config.py            # settings (.env)
│   ├── database.py          # engine + session SQLAlchemy async
│   ├── models.py            # User, Task, TaskAssignment
│   ├── schemas.py           # schémas Pydantic
│   ├── websocket_manager.py # gestion des connexions + broadcast
│   ├── overdue_worker.py    # boucle de fond : détecte les tâches en retard
│   ├── security.py          # dépendance X-API-Key
│   ├── routers/
│   │   ├── users.py
│   │   ├── tasks.py
│   │   ├── dashboard.py
│   │   └── ws.py
│   └── static/
│       ├── dashboard/
│       │   └── index.html   # écran TV (temps réel + son)
│       └── admin/
│           └── index.html   # back-office (CRUD personnel/tâches, pilotage)
├── alembic/                 # migrations (à générer)
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## 6. Roadmap

- **Phase 1 (fait)** : CRUD Personnel/Tâches, affectation, calcul du temps
  restant, WebSocket, dashboard TV avec son, back-office (`/admin`), archivage,
  statut "en retard" automatique (`overdue_worker.py`), clé API partagée.
- **Phase 2** : Auth JWT par utilisateur + rôles sur le back-office, token sur le
  WebSocket pour consommateurs externes.
- **Phase 3** : Passerelle Arduino (`apps/arduino-bridge/`), intégration API tierces.
- **Phase 4** : Reporting / historique / export.
