# TaskBoard

Gestion et suivi de tâches en temps réel : personnel, tâches avec minuteur,
affectation, dashboard TV avec temps restant et alertes sonores, back-office
de pilotage. Architecture monolithique Python (FastAPI), pensée API-first pour
une future intégration avec d'autres applications et un kit Arduino.

Voir `docs/ADR.md` (décisions d'architecture) et `docs/CONCEPTION.md` (modèle
de données, API, WebSocket, roadmap).

## Démarrage rapide

```bash
cp .env.example .env
docker compose up --build
```

- API : http://localhost:8000 (doc interactive sur `/docs`)
- Back-office (créer personnel/tâches, piloter) : http://localhost:8000/admin
- Écran de suivi (dashboard TV) : http://localhost:8000/dashboard
- Santé : http://localhost:8000/health

Les tables sont créées automatiquement au démarrage en dev (`init_db`). Pour la
prod, mettre en place Alembic (`alembic init alembic`) et retirer `init_db()`.

## Clé API

Toutes les routes d'écriture (`POST`/`PATCH` sur `/users` et `/tasks`) exigent
l'en-tête `X-API-Key`, avec la valeur définie dans `.env` (`API_KEY`). Les
routes de lecture (`GET`) restent ouvertes (écran TV interne). Le back-office
(`/admin`) demande la clé une fois et la garde en `localStorage`.

## Tester rapidement le flux

```bash
# 1. Créer une personne
curl -X POST localhost:8000/api/v1/users -H "Content-Type: application/json" \
  -H "X-API-Key: change-me-service-key" \
  -d '{"nom":"Diallo","prenom":"Awa","role":"employe"}'

# 2. Créer une tâche de 10 minutes affiliée à cette personne (remplacer USER_ID)
curl -X POST localhost:8000/api/v1/tasks -H "Content-Type: application/json" \
  -H "X-API-Key: change-me-service-key" \
  -d '{"titre":"Préparer le rapport","minutes_allouees":10,"user_ids":["USER_ID"]}'

# 3. Démarrer la tâche (remplacer TASK_ID) — le dashboard TV se met à jour en direct
curl -X POST localhost:8000/api/v1/tasks/TASK_ID/start -H "X-API-Key: change-me-service-key"

# 4. Terminer la tâche — déclenche le toast + le son côté écran
curl -X POST localhost:8000/api/v1/tasks/TASK_ID/complete -H "X-API-Key: change-me-service-key"
```

Ouvrez `/dashboard` et/ou `/admin` dans un onglet pendant ces appels pour voir
les mises à jour temps réel et entendre les alertes. Une tâche `en_cours` dont
l'échéance est dépassée passe automatiquement en `en_retard` (vérification
toutes les 15s, voir `app/overdue_worker.py`) et diffuse l'événement
`task.overdue`.

## Structure

Voir `docs/CONCEPTION.md` §5.

## Prochaines étapes (phase 2)

- Authentification JWT + rôles par utilisateur sur le back-office (aujourd'hui :
  une clé API partagée protège les écritures, voir ci-dessus).
- Passerelle Arduino (`apps/arduino-bridge/`) — voir ADR-003.
- Authentification/token sur le WebSocket pour des consommateurs externes.
- Reporting / historique / export.
