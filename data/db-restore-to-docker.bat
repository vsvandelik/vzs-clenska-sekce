@echo off
docker cp "%~dp0db.json" vzs-clenska-sekce-backend:/usr/src/app/data/db.json
docker exec vzs-clenska-sekce-backend sh -c "/usr/src/app/data/db-restore.sh"
