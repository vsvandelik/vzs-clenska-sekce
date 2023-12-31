@echo off
python "%~dp0manage.py" loaddata "%~dp0data\db.json"
