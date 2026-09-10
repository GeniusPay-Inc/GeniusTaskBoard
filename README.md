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
- Back-office : http://localhost:8000/admin — menu **Dashboard** (récapitulatif,
  alertes de retard, charge de travail), **Tâches** (Kanban glisser-déposer) et
  **Employés** (personnel + photo de profil)
- Écran de suivi (dashboard TV) : http://localhost:8000/dashboard
- Santé : http://localhost:8000/health

Les tables sont créées automatiquement au démarrage en dev (`init_db`). Pour la
prod, mettre en place Alembic (`alembic init alembic`) et retirer `init_db()`.
Les photos de profil sont stockées sur disque dans `app/static/uploads/`
(non versionné) — prévoir un stockage objet (S3, etc.) et un volume persistant
si l'API tourne sur plusieurs instances ou est redéployée sans volume partagé.

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

## Déploiement — task.geniuspay.tech

Le domaine `task.geniuspay.tech` est prévu pour l'instance de production. Le
`docker-compose.yml` inclut un service **Caddy** qui reçoit le trafic sur les
ports 80/443, obtient et renouvelle automatiquement le certificat TLS
(Let's Encrypt) pour ce domaine, et reverse-proxy vers l'API interne.

1. Pointer un enregistrement DNS `A` (et `AAAA` si IPv6) de `task.geniuspay.tech`
   vers l'IP publique du serveur.
2. Sur le serveur :
   ```bash
   cp .env.example .env
   # vérifier/ajuster dans .env :
   #   DOMAIN=task.geniuspay.tech
   #   CORS_ORIGINS=...,https://task.geniuspay.tech
   #   API_KEY, JWT_SECRET → générer des valeurs fortes (ne pas garder les defaults)
   docker compose up --build -d
   ```
3. Une fois le certificat émis (quelques secondes après le premier accès) :
   - Back-office : https://task.geniuspay.tech/admin
   - Écran de suivi (TV) : https://task.geniuspay.tech/dashboard
   - API / docs : https://task.geniuspay.tech/docs

Le port 8000 de l'API reste aussi publié directement (utile en debug local),
mais en production seul le trafic via Caddy (443) doit être exposé au public
— fermer le port 8000 au niveau du pare-feu du serveur.

## Identité visuelle

- Icônes : [Lucide](https://lucide.dev) chargé en CDN (`<i data-lucide="...">` +
  `lucide.createIcons()`), aucune dépendance locale à installer.
- Logo : le lockup GeniusPay (`Genius` + badge `Pay`) est recréé en HTML/CSS
  directement dans les en-têtes (`.gp-logo`), pas une image — facile à retoucher.
  Police **Poppins** (900) en CDN Google Fonts pour se rapprocher du rendu
  arrondi du logo officiel.
- Mascotte **Geni** : `app/static/shared/geni.js` + `geni.css`, servis via le
  mount `/assets`. C'est le composant SVG fourni par GeniusPay, réécrit en JS
  natif (le projet est un site statique FastAPI, sans Laravel/Alpine) :
  `Geni.mount(el, { state: 'idle' | 'welcome' | 'thinking' | 'loading' | 'success', size: 'xs'..'xl' })`.
  Utilisée aujourd'hui dans l'état vide de l'écran TV et la bannière « aucun
  retard » du dashboard back-office.
- Thème **jour/nuit** (noir & blanc à plat, sans dégradé) : bouton ☀️/🌙 dans
  les deux en-têtes, préférence mémorisée en `localStorage`. Les seules
  couleurs qui subsistent sont fonctionnelles (rouge = retard, vert = ok,
  ambre = attention) ; le décor (fonds, logo, sections) est strictement à plat.

## Annonces vocales et mise en avant (écran TV)

L'écran de suivi (`/dashboard`) parle via la Web Speech API du navigateur
(`speechSynthesis`, voix française si disponible) :
- à la fin d'une tâche : *« *Prénom* a terminé la tâche : *titre*. »*
- quand il reste moins de 5 minutes sur une tâche en cours : *« Attention, il
  reste moins de cinq minutes pour la tâche *titre*, confiée à *Prénom*. »*
  (déclenché une seule fois par tâche)

Les navigateurs bloquent le son tant qu'il n'y a pas eu d'interaction : un
bandeau « Activer le son » apparaît au chargement — à cliquer une fois sur
l'écran TV pour débloquer les annonces et les bips.

Chaque tâche terminée déclenche aussi un **spotlight** : une carte plein
écran (photo/avatar mis en grand plan avec un anneau pulsé, titre, personnel,
temps alloué) reprenant le style des gabarits fournis (bandeau coloré, champs
clé/valeur), affichée ~7s puis enchaînée avec la suivante si plusieurs tâches
se terminent d'affilée. Si la tâche est terminée dans les délais, un badge
« +10 points gagnés » s'affiche et la voix l'annonce. Le spotlight inclut
aussi un **récapitulatif** des autres tâches encore actives (« Pendant ce
temps… ») avec le prénom, le titre et le temps restant de chaque personne pas
encore terminée, annoncé oralement à la suite.

## Points de ponctualité

Chaque tâche terminée dans le temps qui lui était alloué (`date_fin_reelle`
≤ `date_fin_prevue`) rapporte **10 points** à chaque personne affiliée
(`User.points`, cumulé côté serveur dans `POST /tasks/{id}/complete`). Les
points sont consultables :
- sur chaque fiche employé (back-office, vue `Employés`) ;
- dans un mini classement trié par points (back-office, vue `Dashboard` →
  « Classement — points de ponctualité ») ;
- via l'API (`points` dans `GET /api/v1/users`).

## Tableau Kanban et archives

Le tableau (`Tâches`) a 5 colonnes : À faire, En cours, En retard, Terminées,
Archivées. Le glisser-déposer gère tous les déplacements qui ont un sens
métier (démarrer, terminer, archiver, restaurer une tâche archivée vers
« À faire ») ; un déplacement sans action correspondante affiche un message
explicatif au lieu d'échouer silencieusement.

La vue `Archives` liste les tâches archivées avec recherche par titre, filtre
par personnel affilié et tri par date d'archivage (`updated_at`) ou par
titre — chaque tâche peut y être restaurée en un clic.

## Structure

Voir `docs/CONCEPTION.md` §5.

## Prochaines étapes (phase 2)

- Authentification JWT + rôles par utilisateur sur le back-office (aujourd'hui :
  une clé API partagée protège les écritures, voir ci-dessus).
- Passerelle Arduino (`apps/arduino-bridge/`) — voir ADR-003.
- Authentification/token sur le WebSocket pour des consommateurs externes.
- Reporting / historique / export.
