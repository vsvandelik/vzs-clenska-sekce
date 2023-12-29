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
|   ├── :ref:`db.json <data/>`
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
| ├── :ref:`.env`
| ├── :ref:`.env.dist`
| ├── :ref:`.env_psql`
| ├── :ref:`.gitignore`
| ├── :ref:`.pre-commit-config.yaml`
| ├── :ref:`Caddyfile`
| ├── :ref:`docker-build.bat`
| ├── :ref:`docker-build.sh`
| ├── :ref:`docker-compose.yaml`
| ├── :ref:`Dockerfile`
| ├── :ref:`manage.py`
| ├── :ref:`package.json`
| ├── :ref:`package-lock.json`
| ├── :ref:`README.md`
| ├── :ref:`requirements.txt`
| ├── :ref:`requirements_dev.txt`
| ├── :ref:`requirements_prod.txt`

.. _.github/:
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

.. _data/:
---------------------
data/
---------------------
Testovací data, více informací o použití testovací dat viz :ref:`testing`.


.. _docs/:
---------------------
docs/
---------------------
Zdrojový kód této dokumentace.

.. _events/:
---------------------
events/
---------------------
Django aplikace :ref:`events`.

.. _features/:
---------------------
features/
---------------------
Django aplikace :ref:`features`.

.. _google_integration/:
---------------------
google_integration/
---------------------
Obsahuje nezbytné komponenty pro integraci skupin v rámci :term:`IS` a Google Workspace.

.. _groups/:
---------------------
groups/
---------------------
Django aplikace :ref:`groups`.

.. _node_modules/:
---------------------
node_modules/
---------------------
Adresář Node.js obsahující frontendové závislosti.

.. _one_time_events/:
---------------------
one_time_events/
---------------------
Django aplikace :ref:`one_time_events`.

.. _overriden_django_commands/:
---------------------
overriden_django_commands/
---------------------
Adresář určený pro sdružování kódu redefinující výchozí funkcionalitu Djanga. Konkrétně se zde nachází pouze kód redefinující redefinující příkaz ``python ./manage.py createsuperuser`` tak, aby nově vytvořený administrátor měl všechna oprávnění.

.. _pages/:
---------------------
pages/
---------------------
Django aplikace :ref:`pages`.

.. _persons/:
---------------------
persons/
---------------------
Django aplikace :ref:`persons`.

.. _positions/:
---------------------
positions/
---------------------
Django aplikace :ref:`positions`.

.. _static/:
---------------------
static/
---------------------
Sdružuje statický obsah (CSS, JS, obrázky, ...) relevantní pro více Django aplikací, případně pro celý :term:`IS`.

.. _templates/:
---------------------
templates/
---------------------
Sdružuje HTML šablony relevantní pro více Django aplikací, případně pro celý :term:`IS`.

.. _trainings/:
---------------------
trainings/
---------------------
Django aplikace :ref:`trainings`.

.. _transactions/:
---------------------
transactions/
---------------------
Django aplikace :ref:`transactions`.

.. _users/:
---------------------
users/
---------------------
Django aplikace :ref:`users`.

.. _vzs/:
---------------------
vzs/
---------------------
Django aplikace :ref:`vzs`.

.. _.env:
---------------------
.env
---------------------
Environmentální proměnné, které mění konfiguraci :term:`IS`.

.. _.env.dist:
---------------------
.env.dist
---------------------
Šablona, podle které je možné vytvořit soubor ``.env``.

.. _.env_caddy:
---------------------
.env_caddy
---------------------
Environmentální proměnné pro reverse proxy Caddy, relevantní pouze při produkčním nasazení.

.. _.env_psql:
---------------------
.env_psql
---------------------
Environmentální proměnné pro DB systém PostgreSQL, relevantní pouze při produkčním nasazení.

.. _.gitignore:
---------------------
.gitignore
---------------------
Určuje, které soubory mají být ignorovány při práci s verzovacím systémem Git.

.. _.pre-commit-config.yaml:
------------------------
.pre-commit-config.yaml
------------------------
Konfigurační soubor pro framework pre-commit, který spouští nadefinované hooks před provedením příkazu ``git commit``. Soubor je nakonfigurován tak, že před každým commitem se provede formátování Python souborů pomocí Black code formatter, soubory HTML/CSS/JS jsou formátovány pomocí djhtml, které umí formátovat Jinja kód.

.. _Caddyfile:
------------------------
Caddyfile
------------------------
Konfigurační soubor pro reverse proxy Caddy, relevantní pouze při produkčním nasazení.

.. _docker-build.bat:
------------------------
docker-build.bat
------------------------
Batch script, který sestaví docker image pro :term:`IS`.

.. _docker-build.sh:
------------------------
docker-build.sh
------------------------
Shell script, který sestaví docker image pro :term:`IS`.

.. _docker-compose.yaml:
------------------------
docker-compose.yaml
------------------------
Docker compose skript, který vytvoří kontejner ochestrací images :term:`IS`, PostgreSQL a Caddy.

.. _Dockerfile:
------------------------
Dockerfile
------------------------
Soubor popisující, jak sestavit docker image pro :term:`IS`.

.. _manage.py:
------------------------
manage.py
------------------------
Python skript vytvořený Djangem při vytváření nového projektu. Slouží k interakci a správě Django projektu.

.. _package.json:
------------------------
package.json
------------------------
Manifest Node.js projektu, který definuje frontendové závislosti (Bootstrap, Select2, jQuery, ...)

.. _package-lock.json:
------------------------
package-lock.json
------------------------
Automaticky generovaný soubor Node.js projektu, který obsahuje reprodukovatelného popisu stromu závislostí.

.. _README.md:
------------------------
README.md
------------------------
Readme soubor obsahující základní informace o projektu.

.. _requirements.txt:
------------------------
requirements.txt
------------------------
Závislosti projektu, které je nutné mít vždy nainstalované. 

Pro bližší informace o závislostech viz :ref:`dependencies_from_requirements.txt`.

.. _requirements_dev.txt:
------------------------
requirements_dev.txt
------------------------
Závislosti projektu, které nejsou nutné pro spuštění projektu ale jsou povinné pro vývoj (pre-commit, sphinx, ...). 

Pro bližší informace o závislostech viz :ref:`dependencies_from_requirements_dev.txt`.

.. _requirements_prod.txt:
------------------------
requirements_prod.txt
------------------------
Závislosti projektu, které jsou vyžadovány pouze pro běh v produkčním prostředí.

Pro bližší informace o závislostech viz :ref:`dependencies_from_requirements_prod.txt`.

***************************************
Standardní struktura Django aplikace
***************************************
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
| ├── cron.py
| ├── forms.py
| ├── models.py
| ├── permissions.py
| ├── apps.py
| ├── tests.py
| ├── urls.py
| ├── utils.py
| ├── views.py

.. _management/:
------------------------
management/
------------------------
Součástí je vždy podadresář ``commands/``, který sdružuje vlastní Django příkazy, které interagují s aplikací. Tyto příkazy je možné spustit pomocí příkazu ``python ./manage.py <název souboru s příkazem bez koncovky>``, ukázka výše obsahuje dva příkazy ``cmd1.py`` a ``cmd2.py``, ty je možné spustit konkrétním příkazem

.. code-block:: console

    python ./manage.py cmd1
    python ./manage.py cmd2

:term:`IS` obsahuje několik vlastních Django příkazů. Jedním z nich je příkaz ``python ./manage.py createsuperuser``, který vytvoří administrátora se všemi oprávněními.

.. _migrations/:
------------------------
migrations/
------------------------
Soubory popisující migrace modelu aplikace. Migrace představují způsob, jak změny provedené v modelech přenést do schématu databáze. 

.. _static_app/:
------------------------
static/
------------------------
Sdružuje statický obsah (CSS, JS, obrázky, ...) používané pouze touto aplikací.

.. _templates_app/:
------------------------
templates/
------------------------
Sdružuje HTML šablony používané pouze touto aplikací.

.. _templatetags/:
------------------------
templatetags/
------------------------
Vlastní šablonové tagy využívané pouze v rámci aplikace pro Jinja renderovací engine Djanga. Neplatí pro aplikace :ref:`events` a :ref:`vzs`. První zmíněná sdružuje kód jednorázových událostí (aplikace :ref:`one_time_events`) a tréninků (aplikace :ref:`trainings`). Druhá zmíněná obsahuje společný kód využívaný všemi ostatními aplikacemi.

.. _apps.py:
------------------------
apps.py
------------------------
Slouží ke konfiguraci chování aplikace, je zde možné nastavit např. jiné jméno aplikace apod.

