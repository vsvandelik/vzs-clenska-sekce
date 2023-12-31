@echo off
python "%~dp0manage.py" dumpdata --exclude=auth --exclude=contenttypes > "%~dp0data\db.json"
