@echo off
python "%~dp0..\manage.py" dumpdata --exclude=auth --exclude=contenttypes > "%~dp0db.json"
