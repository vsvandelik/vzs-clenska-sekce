##########################
Instalační dokumentace
##########################
V tomto dokumentu jsou detailně popsány všechny scénáře spouštění a nasazení projektu včetně produkčního nasazení.

V celém tomto dokumentu předpokládáme, že se v terminálu nacházíme v kořenovém adresáři projektu.

***************************************
Lokální debug spuštění
***************************************
Lokální debug spuštění je vhodné, pokud nám stačí projekt na spustit na lokálním prostředí. Je nutné si uvědomit, že při tomto spuštění je použit vestavěný webový server Djanga, který není určen pro produkční nasazení a SQLite, jehož použití není optimální při paralelních přístupech.

Prerekvizity
------------
- Python ≥ 3.11 
- ``pip``

Před prvním spuštění je nutné provést konfiguraci a nainstalovat závislosti.

1. Nastavíme obsah souboru ``.env`` jako

.. code-block:: console

    DEBUG=True 
    SECRET_KEY=django-insecure
    GOOGLE_DOMAIN= 
    FIO_TOKEN= 


2. Vytvoříme virtuální prostředí

.. code-block:: console

    python -m venv venv

3. Aktivujeme virtuální prostředí

.. code-block:: console

    source venv/bin/activate  (Linux)

    venv\Scripts\activate.bat  (Windows)

4. Nainstalujeme závislosti nutné ke spuštění

.. code-block:: console

    pip install -r requirements.txt


|

Nyní je možné spustit webový server Djanga.

.. code-block:: console

     python manage.py runserver 8080


    
***************************************
Lokální test produkčního nasazení
***************************************
Tento druh spuštění je vhodný v případě, kdy chceme otestovat funkčnost projektu při použítí všech částí produkčního nasazení (Gunicorn, PostgreSQL, Caddy) vyjma HTTPS.

Prerekvizity
------------
- docker ≥ 1.13.1


Před vytvořením docker image je nutné provést konfiguraci.

1. Nastavíme obsah souboru ``.env`` jako

.. code-block:: console

    DEBUG=True
    SECRET_KEY=django-insecure
    GOOGLE_DOMAIN=
    FIO_TOKEN=

    SQL_ENGINE=django.db.backends.postgresql
    SQL_DATABASE=vzs-clenska-sekce
    SQL_USER=vzs
    SQL_PASSWORD=supersecret
    SQL_HOST=db
    SQL_PORT=5432

2. Nastavíme proměnné o stejných hodnotách i z pohledu PostgreSQL. Soubor ``.env_psql`` by měl vypadat takto

.. code-block:: console

    POSTGRES_USER=vzs
    POSTGRES_PASSWORD=supersecret
    POSTGRES_DB=vzs-clenska-sekce

3. Nastavíme konfigurační soubor ``Caddyfile`` pro reverzní proxy Caddy

.. code-block:: console

    {
        auto_https disable_redirects
    }

    http://localhost:80 {
        handle_path /static/* {
            root * /var/www/staticfiles
            file_server
        }
        reverse_proxy vzs-clenska-sekce-backend:8080
    }


Poté můžeme sestavit docker image projektu.

.. code-block:: console

    ./docker-build.sh  (Linux)

    docker-build.bat  (Windows)


Nyní můžeme celý projekt spustit jedním příkazem

.. code-block:: console

    docker compose up

***************************************
Produkční nasazení
***************************************