@echo off
docker exec vzs-clenska-sekce-backend sh -c "/usr/src/app/data/db-backup.sh"
docker cp vzs-clenska-sekce-backend:/usr/src/app/data/db.json "%~dp0db.json"
