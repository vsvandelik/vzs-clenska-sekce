@echo off
python "%~dp0..\manage.py" loaddata "%~dp0db.json"
