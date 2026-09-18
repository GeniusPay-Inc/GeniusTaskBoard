#!/usr/bin/env bash
set -euo pipefail

# Migration unique — UNIQUEMENT pour un déploiement via docker-compose sur un
# serveur/VPS géré à la main. Ne concerne PAS un déploiement sur une
# plateforme managée type Railway/Render/Fly.io, qui ne lit pas
# docker-compose.yml et pour laquelle le stockage persistant se configure
# depuis le dashboard de la plateforme (voir le README, section
# « Déploiement »).
#
# Bascule les données de l'ancien schéma (bind mounts ./data et ./uploads,
# effacés par un git clean/reset du dossier projet) vers le volume Docker
# nommé taskboard_data, qui survit à un git pull, un git clean, voire un
# nouveau clone du dépôt. Les photos (auparavant dans ./uploads) sont
# désormais stockées sous data/uploads, dans ce même volume.
#
# À lancer UNE SEULE FOIS sur le serveur, après avoir récupéré le nouveau
# docker-compose.yml (git pull). Sans danger à relancer plusieurs fois : si
# ./data/taskboard.db n'existe pas (neuf, ou déjà migré), le script ne fait
# rien.

cd "$(dirname "$0")/.."

if [ ! -f "./data/taskboard.db" ]; then
  echo "Aucun ./data/taskboard.db trouvé — rien à migrer (installation neuve, ou déjà migrée)."
  exit 0
fi

echo "→ Démarrage du service api (crée le volume taskboard_data s'il n'existe pas encore)…"
docker compose up -d api

echo "→ Copie de la base SQLite existante vers le volume nommé…"
docker compose cp "./data/taskboard.db" api:/app/data/taskboard.db

if [ -d "./uploads" ] && [ -n "$(ls -A ./uploads 2>/dev/null)" ]; then
  echo "→ Copie des photos de profil existantes vers le volume nommé (data/uploads)…"
  docker compose exec -T api mkdir -p /app/data/uploads/avatars
  docker compose cp "./uploads/." api:/app/data/uploads/
fi

echo "→ Redémarrage de l'API pour repartir sur les données migrées…"
docker compose restart api

echo
echo "✓ Migration terminée. Vérifiez sur /admin que le personnel et les tâches"
echo "  sont bien là, puis vous pouvez supprimer ./data et ./uploads du dossier"
echo "  du projet — les données vivent désormais dans le volume Docker"
echo "  taskboard_data, indépendant du dossier et donc insensible à un git pull/clean."
