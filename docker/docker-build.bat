@echo off
setlocal
set "olddir=%cd%"
set "dockerdir=%~dp0"
set "dockerfile=%~dp0Dockerfile"
cd /d "%dockerdir%"
cd /d ..
set "projectdir=%cd%"
docker build -t vzs-clenska-sekce "%projectdir%" -f "%dockerfile%"
cd /d "%olddir%"
endlocal
