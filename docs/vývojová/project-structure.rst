***************************************
Struktura projektu
***************************************

Projekt obsahuje mnoho souborů a adresářů, jejichž význam popíšeme zde.

---------------------------------------
Stromová struktura
---------------------------------------

Pořadí je vzestupné podle abecedy, první jsou adresáře, které jsou zakončeny lomítkem, za nimi následují soubory.

| vzs-clenska-sekce
| ├── :ref:`.github/`
|   ├── :ref:`workflows <.github/>`
|     ├── :ref:`deploy.yml <.github/>`
|     ├── :ref:`django.yml <.github/>`
|     ├── :ref:`docs.yml <.github/>`
| ├── :ref:`api/`
| ├── :ref:`data/`
|   ├── :ref:`data/db.json`
|   ├── :ref:`data/db-backup.bat`
|   ├── :ref:`data/db-backup.sh`
|   ├── :ref:`data/db-restore.bat`
|   ├── :ref:`data/db-restore.sh`
| ├── :ref:`docker/`
|   ├── :ref:`docker/.env_caddy`
|   ├── :ref:`docker/.env_psql`
|   ├── :ref:`docker/docker-build.bat`
|   ├── :ref:`docker/docker-build.sh`
|   ├── :ref:`docker/docker-compose.yaml`
|   ├── :ref:`docker/Dockerfile`
| ├── :ref:`docs/`
| ├── :ref:`events/`
| ├── :ref:`features/`
| ├── :ref:`google_integration/`
| ├── :ref:`groups/`
| ├── :ref:`node_modules/`
| ├── :ref:`one_time_events/`
| ├── :ref:`overriden_django_commands/`
| ├── :ref:`pages/`
| ├── :ref:`persons/`
| ├── :ref:`positions/`
| ├── :ref:`static/`
| ├── :ref:`templates/`
| ├── :ref:`trainings/`
| ├── :ref:`transactions/`
| ├── :ref:`users/`
| ├── :ref:`vzs/`
| ├── :ref:`.dockerignore`
| ├── :ref:`.env`
| ├── :ref:`.env.dist`
| ├── :ref:`.gitignore`
| ├── :ref:`.pre-commit-config.yaml`
| ├── :ref:`manage.py`
| ├── :ref:`package.json`
| ├── :ref:`package-lock.json`
| ├── :ref:`README.md`
| ├── :ref:`requirements.txt`
| ├── :ref:`requirements_dev.txt`
| ├── :ref:`requirements_prod.txt`

.. _.github/:

.github/
^^^^^^^^^^^^^^^^^^
Workflows pro GitHub. Konkrétně:

- Deploy to VPS (nasadí aktuální master větev na testovací VPS server)
- Deploy static content to Pages (nasadí aktuální dokumentaci na GitHub Pages)
- Django CI (zkontroluje, zda nedojde k chybě při spuštění migrací)

.. _api/:

api/
^^^^^^^^^^^^^^^^^^

Django aplikace :ref:`api`.

.. _data/:

data/
^^^^^^^^^^^^^^^^^^
Adresář obsahující testovací data a skripty pro zálohu a obnovení databáze.

.. _data/db.json:

data/db.json
^^^^^^^^^^^^^
Testovací data, více informací o použití testovací dat viz :ref:`testing`.


.. _data/db-backup.bat:

data/db-backup.bat
^^^^^^^^^^^^^^^^^^^
Windows Batch script pro zálohu databáze.

.. _data/db-backup.sh:

data/db-backup.sh
^^^^^^^^^^^^^^^^^^^
Shell script pro zálohu databáze.

.. _data/db-restore.bat:

data/db-restore.bat
^^^^^^^^^^^^^^^^^^^^
Windows Batch script pro obnovu databáze.

.. _data/db-restore.sh:

data/db-restore.sh
^^^^^^^^^^^^^^^^^^^
Shell script pro obnovu databáze.

.. _docker/:

docker/
^^^^^^^^^^^^^^^^^^
Soubory k sestavení docker image a orchestraci.

.. _docker/.env_caddy:

docker/.env_caddy
^^^^^^^^^^^^^^^^^^
Environmentální proměnné pro reverse proxy Caddy, relevantní pouze při produkčním nasazení.

.. _docker/.env_psql:

docker/.env_psql
^^^^^^^^^^^^^^^^^^
Environmentální proměnné pro DB systém PostgreSQL, relevantní pouze při produkčním nasazení.

.. _docker/Caddyfile:

docker/Caddyfile
^^^^^^^^^^^^^^^^^^
Konfigurační soubor pro reverse proxy Caddy, relevantní pouze při produkčním nasazení.

.. _docker/docker-build.bat:

docker/docker-build.bat
^^^^^^^^^^^^^^^^^^^^^^^^
Windows Batch script, který sestaví docker image pro :term:`IS`.

.. _docker/docker-build.sh:

docker/docker-build.sh
^^^^^^^^^^^^^^^^^^^^^^^^
Shell script, který sestaví docker image pro :term:`IS`.

.. _docker/docker-compose.yaml:

docker/docker-compose.yaml
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Docker compose skript, který vytvoří kontejner ochestrací images :term:`IS`, PostgreSQL a Caddy.

.. _docker/Dockerfile:

docker/Dockerfile
^^^^^^^^^^^^^^^^^^^^^^^^
Soubor popisující, jak sestavit docker image pro :term:`IS`.


.. _docs/:

docs/
^^^^^^^^^^^^^^^^^^
Zdrojový kód této dokumentace.

.. _events/:

events/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`events`.

.. _features/:

features/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`features`.

.. _google_integration/:

google_integration/
^^^^^^^^^^^^^^^^^^^^
Obsahuje nezbytné komponenty pro integraci skupin v rámci :term:`IS` a Google Workspace.

.. _groups/:

groups/
^^^^^^^^^^^^^^^^^^^^

Django aplikace :ref:`groups`.

.. _node_modules/:

node_modules/
^^^^^^^^^^^^^^^^^^
Adresář Node.js obsahující frontendové závislosti.

.. _one_time_events/:

one_time_events/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`one_time_events`.

.. _overriden_django_commands/:

overriden_django_commands/
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Adresář určený pro sdružování kódu redefinující výchozí funkcionalitu Djanga. Konkrétně se zde nachází pouze kód redefinující redefinující příkaz ``python ./manage.py createsuperuser`` tak, aby nově vytvořený administrátor měl všechna povolení.

.. _pages/:

pages/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`pages`.

.. _persons/:

persons/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`persons`.

.. _positions/:

positions/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`positions`.

.. _static/:

static/
^^^^^^^^^^^^^^^^^^
Sdružuje statický obsah (CSS, JS, obrázky, ...) relevantní pro více Django aplikací, případně pro celý :term:`IS`.

.. _templates/:

templates/
^^^^^^^^^^^^^^^^^^
Sdružuje HTML šablony relevantní pro více Django aplikací, případně pro celý :term:`IS`.

.. _trainings/:

trainings/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`trainings`.

.. _transactions/:

transactions/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`transactions`.

.. _users/:

users/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`users`.

.. _vzs/:

vzs/
^^^^^^^^^^^^^^^^^^
Django aplikace :ref:`vzs`.

.. _.dockerignore:

.dockerignore
^^^^^^^^^^^^^^^^^^
TODO napsat neco

.. _.env:

.env
^^^^^^^^^^^^^^^^^^
Environmentální proměnné, které mění konfiguraci :term:`IS`.

.. _.env.dist:

.env.dist
^^^^^^^^^^^^^^^^^^
Šablona, podle které je možné vytvořit soubor ``.env``.

.. _.gitignore:

.gitignore
^^^^^^^^^^^^^^^^^^
Určuje, které soubory mají být ignorovány při práci s verzovacím systémem Git.

.. _.pre-commit-config.yaml:

.pre-commit-config.yaml
^^^^^^^^^^^^^^^^^^^^^^^^
Konfigurační soubor pro framework pre-commit, který spouští nadefinované hooks před provedením příkazu ``git commit``. Soubor je nakonfigurován tak, že před každým commitem se provede formátování Python souborů pomocí Black Code Formatter, soubory HTML/CSS/JS jsou formátovány pomocí djhtml, které umí formátovat Jinja kód.

.. _manage.py:

manage.py
^^^^^^^^^^^^^^^^^^
Python skript vytvořený Djangem při vytváření nového projektu. Slouží k interakci a správě Django projektu.

.. _package.json:

package.json
^^^^^^^^^^^^^^^^^^
Manifest Node.js projektu, který definuje frontendové závislosti (Bootstrap, Select2, jQuery, ...)

.. _package-lock.json:

package-lock.json
^^^^^^^^^^^^^^^^^^
Automaticky generovaný soubor Node.js projektu, který obsahuje reprodukovatelného popisu stromu závislostí.

.. _README.md:

README.md
^^^^^^^^^^^^^^^^^^
Readme soubor obsahující základní informace o projektu.

.. _requirements.txt:

requirements.txt
^^^^^^^^^^^^^^^^^^
Závislosti projektu, které je nutné mít vždy nainstalované. 

Pro bližší informace o závislostech viz :ref:`dependencies_from_requirements.txt`.

.. _requirements_dev.txt:

requirements_dev.txt
^^^^^^^^^^^^^^^^^^^^^^
Závislosti projektu, které nejsou nutné pro spuštění projektu ale jsou povinné pro vývoj (pre-commit, sphinx, ...). 

Pro bližší informace o závislostech viz :ref:`dependencies_from_requirements_dev.txt`.

.. _requirements_prod.txt:

requirements_prod.txt
^^^^^^^^^^^^^^^^^^^^^^
Závislosti projektu, které jsou vyžadovány pouze pro běh v produkčním prostředí.

Pro bližší informace o závislostech viz :ref:`dependencies_from_requirements_prod.txt`.

-------------------------------------
Standardní struktura Django aplikace
-------------------------------------
Zde si popíšeme jak zhruba vypadá struktura libovolné Django aplikace :term:`IS`. Tato struktura přímo odpovídá konvencím Djanga, proto informace obsažené v této sekci neobsahují příliš mnoho nových informací pro osoby dobře znalé Djanga.

| django-aplikace
| ├── :ref:`management/`
|   ├── :ref:`commands/ <management/>`
|     ├── :ref:`__init__.py <management/>`
|     ├── :ref:`cmd1.py <management/>`
|     ├── :ref:`cmd2.py <management/>`
|     ├── ...
| ├── :ref:`migrations/`
| ├── :ref:`static_app/`
| ├── :ref:`templates_app/`
| ├── :ref:`templatetags/`
| ├── __init__.py
| ├── :ref:`apps.py`
| ├── :ref:`cron.py`
| ├── :ref:`forms.py`
| ├── :ref:`models.py`
| ├── :ref:`permissions.py`
| ├── :ref:`urls.py`
| ├── :ref:`utils.py`
| ├── :ref:`views.py`

.. _management/:

management/
^^^^^^^^^^^^^^^^^^
Součástí je vždy podadresář ``commands/``, který sdružuje vlastní Django příkazy, které interagují s aplikací. Bližší informace ohledně vytvoření vlastního Django příkazu jsou k dispozici na stránce :ref:`vytvoreni_vlastniho_django_prikazu`.

:term:`IS` obsahuje několik vlastních Django příkazů. Kompletní seznam je k dispozici na stránce :ref:`vlastni_django_prikazy`.

.. _migrations/:

migrations/
^^^^^^^^^^^^^^^^^^
Soubory popisující migrace modelu aplikace. Migrace představují způsob, jak změny provedené v modelech přenést do schématu databáze. 

.. _static_app/:

static/
^^^^^^^^^^^^^^^^^^
Sdružuje statický obsah (CSS, JS, obrázky, ...) používané pouze touto aplikací.

.. _templates_app/:

templates/
^^^^^^^^^^^^^^^^^^
Sdružuje HTML šablony používané pouze touto aplikací.

.. _templatetags/:

templatetags/
^^^^^^^^^^^^^^^^^^
Vlastní šablonové tagy využívané pouze v rámci aplikace pro Jinja renderovací engine Djanga. Neplatí pro aplikace :ref:`events` a :ref:`vzs`. První zmíněná sdružuje kód jednorázových událostí (aplikace :ref:`one_time_events`) a tréninků (aplikace :ref:`trainings`). Druhá zmíněná obsahuje společný kód využívaný všemi ostatními aplikacemi.

.. _apps.py:

apps.py
^^^^^^^^^^^^^^^^^^
Slouží ke konfiguraci chování aplikace, je zde možné nastavit např. jiné jméno aplikace apod.

.. _cron.py:

cron.py
^^^^^^^^^^^^^^^^^^
Funkce, které jsou periodicky volány pomocí daemonu cron, více informací o vytvoření funkce volané Cronem viz :ref:`funkce_volane_daemonem_cron`.

.. _forms.py:

forms.py
^^^^^^^^^^^^^^^^^^
Třídy definující formuláře aplikace, více informací o formulářích víz :ref:`forms`.

.. _models.py:

models.py
^^^^^^^^^^^^^^^^^^
Obsahuje modely aplikace včetně metod, která nad nimi operují.

.. _permissions.py:

permissions.py
^^^^^^^^^^^^^^^^^^
Třídy a metody pracující s oprávněními aplikované na pohledy aplikace.

.. _urls.py:

urls.py
^^^^^^^^^^^^^^^^^^
Obsahuje definice URL vzorů mapující se na jednotlivé pohledy definované ve :ref:`views.py`

.. _utils.py:

utils.py
^^^^^^^^^^^^^^^^^^
Různé pomocné funkce, které aplikace využívá. Aplikace :ref:`events` např. využívá funkci ``parse_czech_date(date_str)``, která parsuje datum ze standardního českého formátu.

.. _views.py:

views.py
^^^^^^^^^^^^^^^^^^
Jednotlivé pohledy ke kterým je možné přistoupit z URL vzorů definovaných v souboru :ref:`urls.py`