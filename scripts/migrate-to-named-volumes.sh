#!/usr/bin/env bash
set -euo pipefail

# Migration unique : bascule les données de l'ancien schéma (bind mounts
# ./data et ./uploads, effacés par un git clean/reset du dossier projet) vers
# les volumes Docker nommés taskboard_data / taskboard_uploads, qui survivent
# à un git pull, un git clean, voire un nouveau clone du dépôt.
#
# À lancer UNE SEULE FOIS sur le serveur de production, après avoir récupéré
# le nouveau docker-compose.yml (git pull). Sans danger à relancer plusieurs
# fois : si ./data/taskboard.db n'existe pas (neuf, ou déjà migré), le script
# ne fait rien.

cd "$(dirname "$0")/.."

if [ ! -f "./data/taskboard.db" ]; then
  echo "Aucun ./data/taskboard.db trouvé — rien à migrer (installation neuve, ou déjà migrée)."
  exit 0
fi

echo "→ Démarrage du service api (crée les volumes taskboard_data / taskboard_uploads s'ils n'existent pas encore)…"
docker compose up -d api

echo "→ Copie de la base SQLite existante vers le volume nommé…"
docker compose cp "./data/taskboard.db" api:/app/data/taskboard.db

if [ -d "./uploads" ] && [ -n "$(ls -A ./uploads 2>/dev/null)" ]; then
  echo "→ Copie des photos de profil existantes vers le volume nommé…"
  docker compose cp "./uploads/." api:/app/app/static/uploads/
fi

echo "→ Redémarrage de l'API pour repartir sur les données migrées…"
docker compose restart api

echo
echo "✓ Migration terminée. Vérifiez sur /admin que le personnel et les tâches"
echo "  sont bien là, puis vous pouvez supprimer ./data et ./uploads du dossier"
echo "  du projet — les données vivent désormais dans des volumes Docker,"
echo "  indépendants du dossier et donc insensibles à un git pull/clean."
