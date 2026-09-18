# Passage en production sur Railway

Ce document est la procédure **définitive et unique** de mise en place du
stockage persistant sur Railway. Une fois suivie, plus aucune donnée
(personnel, tâches, photos, points) ne sera perdue à un redéploiement —
c'est une configuration au niveau du service, pas du code : elle survit à
tous les déploiements futurs (push GitHub, rebuild, redémarrage) sans avoir
à la refaire.

**Sans accès à votre compte Railway, je ne peux pas exécuter ces étapes à
votre place** (pas d'accès dashboard, pas de token API/CLI dans cette
session) — c'est la seule partie de la mise en production qui reste
manuelle. Tout le reste (code, migrations, structure des données) est déjà
en place sur `main`.

## Pourquoi une perte de données est nécessaire une fois

Le code actuel range tout ce qui doit persister (base SQLite, photos,
sauvegardes automatiques) sous un seul dossier : `/app/data`. Tant qu'aucun
volume Railway n'est monté sur ce chemin, ce dossier vit sur le système de
fichiers **éphémère** du conteneur — recréé vide à chaque déploiement. C'est
la cause de toutes les pertes de données observées jusqu'ici.

Attacher un volume à `/app/data` la première fois **remplace** le dossier
éphémère par un volume persistant réel — celui-ci démarre vide. Les données
actuellement en ligne (avant cette manipulation) seront donc perdues **une
dernière fois**. C'est accepté : après cette étape, plus aucune perte.

## Procédure (à faire une seule fois)

1. **Dashboard Railway** → projet `GeniusTask` → environnement `production`
   → service API (`exuberant-eland-...` dans votre capture d'écran).
2. **Settings → Persistent Storage** → *Add Volume* (ou *New Volume*).
3. Définir le point de montage : **`/app/data`** exactement (respecter la
   casse et le chemin absolu).
4. Enregistrer. Railway redéploie automatiquement le service avec le volume
   attaché.
5. Une fois le déploiement terminé (voir **Deployment Logs**), le service
   redémarre avec `/app/data` vide — c'est attendu.

## Vérifier que c'est bien réglé, avant d'y remettre les vraies données

Ne resaisissez pas encore tout le personnel et toutes les tâches réelles.
Vérifiez d'abord que la persistance fonctionne :

1. Ouvrir `https://task.geniuspay.tech/admin` (ou l'URL Railway par défaut
   si le domaine n'est pas encore branché).
2. Créer **une personne de test** (ex. « Test Persistance »).
3. Dans Railway, forcer un redémarrage du service (**Settings → Restart**,
   ou un redeploy manuel depuis **Deployments**).
4. Une fois le service de nouveau `Running`, recharger `/admin` → la
   personne de test doit **toujours être là**.
5. Si oui : la persistance est en place, définitivement. Supprimer la
   personne de test, puis ressaisir (ou réimporter) les vraies données de
   production.
6. Si non (la personne de test a disparu) : le volume n'est pas monté au
   bon chemin — revérifier l'étape 3 (`/app/data`, sans faute de frappe) et
   consulter les **Deployment Logs** pour une éventuelle erreur au
   démarrage.

## Checklist de mise en production (le reste, déjà en place)

- [x] Base + photos + sauvegardes automatiques consolidées sous `data/`
      (une seule racine à rendre persistante) — mergé sur `main`.
- [x] Sauvegarde automatique de la base à chaque démarrage
      (`data/backups/`, 5 dernières conservées) — filet de sécurité
      supplémentaire, pas un substitut au volume.
- [ ] Volume Railway monté sur `/app/data` (étapes ci-dessus — **à faire**).
- [ ] Variables d'environnement en prod (**Settings → Variables** sur
      Railway) — vérifier que `API_KEY` et `JWT_SECRET` sont des valeurs
      fortes générées pour la prod, pas les valeurs par défaut de
      `.env.example` :
      ```bash
      # générer une valeur forte, par ex. :
      openssl rand -hex 32
      ```
- [ ] `CORS_ORIGINS` inclut bien `https://task.geniuspay.tech` (déjà le cas
      dans `.env.example`, à confirmer côté variables Railway).
- [ ] `DOMAIN` réglé sur `task.geniuspay.tech` et domaine personnalisé
      configuré dans **Settings → Domains** côté Railway (TLS géré par
      Railway lui-même sur cette plateforme, pas par Caddy).
- [ ] Après avoir revalidé la persistance (section précédente), ressaisir
      les données réelles de production.

Une fois toutes les cases cochées, le passage en production est terminé et
robuste aux redéploiements futurs.
