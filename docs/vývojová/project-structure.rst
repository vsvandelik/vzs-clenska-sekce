***************************************
Struktura projektu
***************************************

Projekt obsahuje mnoho souborů a adresářů, jejichž význam popíšeme zde.

---------------------------------------
Stromová struktura
---------------------------------------

Pořadí je vzestupné podle abecedy, první jsou adresáře, které jsou zakončeny lomítkem, za nimi následují soubory.

| vzs-clenska-sekce
| ├── .github/
|   ├── workflows
|     ├── deploy.yml
|     ├── django.yml
|     ├── docs.yml
| ├── :ref:`api/`
| ├── data/
|   ├── db.json
| ├── docs/
| ├── events/
| ├── features/
| ├── google_integration/
| ├── groups/
| ├── node_modules/
| ├── one_time_events/
| ├── overriden_django_commands/
| ├── pages/
| ├── persons/
| ├── positions/
| ├── static/
| ├── templates/
| ├── trainings/
| ├── transactions/
| ├── users/
| ├── vzs/
| ├── .env
| ├── .env_dist
| ├── .env_psql
| ├── .gitignore
| ├── .pre-commit-config.yaml
| ├── Caddyfile
| ├── docker-build.bat
| ├── docker-build.sh
| ├── docker-compose.yaml
| ├── Dockerfile
| ├── manage.py
| ├── package.json
| ├── package-lock.json
| ├── README.md
| ├── requirements.txt
| ├── requirements_dev.txt
| ├── requirements_prod.txt

---------------------
.github/
---------------------
Workflows pro GitHub. Konkrétně:

- Deploy to VPS (nasadí aktuální master větev na testovací VPS server)
- Deploy static content to Pages (nasadí aktuální dokumentaci na GitHub Pages)
- Django CI (zkontroluje, zda nedojde k chybě při spuštění migrací)

.. _api/:
---------------------
api/
---------------------
Django aplikace :ref:`api`.

---------------------
data/
---------------------
Testovací data, více informací o použití testovací dat viz :ref:`testing`.


---------------------
docs/
---------------------
Zdrojový kód této dokumentace.

---------------------
events/
---------------------
Django aplikace :ref:`events`.

---------------------
features/
---------------------
Django aplikace :ref:`features`.

---------------------
google_integration/
---------------------
Obsahuje nezbytné komponenty pro integraci skupin v rámci :term:`IS` a Google Workspace.

---------------------
groups/
---------------------
Django aplikace :ref:`groups`.

---------------------
node_modules/
---------------------
Adresář Node.js obsahující frontendové závislosti.

---------------------
one_time_events/
---------------------
Django aplikace :ref:`one_time_events`.

---------------------
overriden_django_commands/
---------------------
Adresář určený pro sdružování kódu redefinující výchozí funkcionalitu Djanga. Konkrétně se zde nachází pouze kód redefinující redefinující příkaz ``python ./manage.py createsuperuser`` tak, aby nově vytvořený administrátor měl všechna oprávnění.

---------------------
pages/
---------------------
Django aplikace :ref:`pages`.

---------------------
persons/
---------------------
Django aplikace :ref:`persons`.

---------------------
positions/
---------------------
Django aplikace :ref:`positions`.

---------------------
static/
---------------------
Sdružuje statický obsah (CSS, JS, obrázky, ...) relevantní pro více Django aplikací, případně pro celý :term:`IS`.

---------------------
templates/
---------------------
Sdružuje HTML šablony relevantní pro více Django aplikací, případně pro celý :term:`IS`.

---------------------
trainings/
---------------------
Django aplikace :ref:`trainings`.

---------------------
transactions/
---------------------
Django aplikace :ref:`transactions`.

---------------------
users/
---------------------
Django aplikace :ref:`users`.

---------------------
vzs/
---------------------
Django aplikace :ref:`vzs`.

---------------------
.env
---------------------
Environmentální proměnné, které mění konfiguraci :term:`IS`.

---------------------
.env.dist
---------------------
Šablona, podle které je možné vytvořit soubor ``.env``.

---------------------
.env_caddy
---------------------
Environmentální proměnné pro reverse proxy Caddy, relevantní pouze při produkčním nasazení.

---------------------
.env_psql
---------------------
Environmentální proměnné pro DB systém PostgreSQL, relevantní pouze při produkčním nasazení.

---------------------
.gitignore
---------------------
Určuje, které soubory mají být ignorovány při práci s verzovacím systémem Git.

------------------------
.pre-commit-config.yaml
------------------------
Konfigurační soubor pro framework pre-commit, který spouští nadefinované hooks před provedením příkazu ``git commit``. Soubor je nakonfigurován tak, že před každým commitem se provede formátování Python souborů pomocí Black code formatter, soubory HTML/CSS/JS jsou formátovány pomocí djhtml, které umí formátovat Jinja kód.

------------------------
Caddyfile
------------------------
Konfigurační soubor pro reverse proxy Caddy, relevantní pouze při produkčním nasazení.

------------------------
docker-build.bat
------------------------
Batch script, který sestaví docker image pro :term:`IS`.

------------------------
docker-build.sh
------------------------
Shell script, který sestaví docker image pro :term:`IS`.

------------------------
docker-compose.yaml
------------------------
Docker compose skript, který vytvoří kontejner ochestrací images :term:`IS`, PostgreSQL a Caddy.

------------------------
Dockerfile
------------------------
Soubor popisující, jak sestavit docker image pro :term:`IS`.

------------------------
manage.py
------------------------
Python skript vytvořený Djangem při vytváření nového projektu. Slouží k interakci a správě Django projektu.

------------------------
package.json
------------------------
Manifest Node.js projektu, který definuje frontendové závislosti (Bootstrap, Select2, jQuery, ...)

------------------------
package-lock.json
------------------------
Automaticky generovaný soubor Node.js projektu, který obsahuje reprodukovatelného popisu stromu závislostí.

------------------------
README.md
------------------------
README soubor obsahující základní informace o projektu.

------------------------
requirements.txt
------------------------
Závislosti projektu, které je nutné mít vždy nainstalované.

------------------------
requirements_dev.txt
------------------------
Závislosti projektu, které nejsou nutné pro spuštění projektu ale jsou povinné pro vývoj (pre-commit, sphinx, ...).

------------------------
requirements_prod.txt
------------------------
Závislosti projektu, které jsou vyžadovány pouze pro běh v produkčním prostředí.

***************************************
Standardní struktura Django aplikace
***************************************
