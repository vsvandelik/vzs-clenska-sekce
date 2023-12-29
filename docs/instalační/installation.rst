V tomto dokumentu jsou detailně popsány všechny scénáře spouštění a nasazení projektu včetně produkčního nasazení.

V celém tomto dokumentu předpokládáme, že se v terminálu nacházíme v kořenovém adresáři projektu.

.. _local-debug:
---------------------------------------
Lokální debug spuštění
---------------------------------------
Lokální debug spuštění je vhodné, pokud nám stačí projekt spustit na lokálním prostředí. Je nutné si uvědomit, že při tomto spuštění je použit vestavěný webový server Djanga, který není určen pro produkční nasazení a SQLite, jehož použití není optimální při paralelních přístupech.

Prerekvizity
------------
- Python ≥ 3.11 
- ``pip``

Před prvním spuštění je nutné provést konfiguraci a nainstalovat závislosti.

1. Překopírujeme soubor ``.env.dist`` do ``.env`` a provedeme nastavení proměnných dle nápovědy u každé proměnné. Doporučujeme vycházet z následujícího nastavení proměnných, pokud jiné hodnoty nejsou k dispozici.

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

5. Spustíme migrace

.. code-block:: console

    python ./manage.py migrate
    
|

Nyní je možné spustit webový server Djanga.

.. code-block:: console

     python ./manage.py runserver 8080


    
---------------------------------------
Lokální test produkčního nasazení
---------------------------------------
Tento druh spuštění je vhodný v případě, kdy chceme otestovat funkčnost projektu při použítí všech částí produkčního nasazení (Gunicorn, PostgreSQL, Caddy) vyjma HTTPS.


Prerekvizity
^^^^^^^^^^^^^
- docker ≥ 1.13.1


Před vytvořením docker image je nutné provést konfiguraci.

1. Překopírujeme soubor ``.env.dist`` do ``.env`` a provedeme nastavení proměnných dle nápovědy u každé proměnné. Doporučujeme vycházet z následujícího nastavení proměnných, pokud jiné hodnoty nejsou k dispozici.

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

.. _production:
---------------------------------------
Produkční nasazení
---------------------------------------
Zde si popíšeme, co všechno je potřeba udělat, abychom mohli projekt bezpečně vystavit na Internet.

Prerekvizity
^^^^^^^^^^^^
- docker ≥ 1.13.1

Nejprve se pustíme do konfigurace. Nahradíme obsah souboru ``.env`` obsahem ze souboru ``.env.dist`` doplníme zbylé nevyplněné proměnné.

.. code-block:: console

    DEBUG=False
    SECRET_KEY=
    GOOGLE_DOMAIN=
    FIO_TOKEN=
    SQL_ENGINE=django.db.backends.postgresql
    SQL_DATABASE=vzs-clenska-sekce
    SQL_USER=vzs
    SQL_PASSWORD=
    SQL_HOST=db
    SQL_PORT=5432

- Nastavení bezpečného hesla do proměnné ``SECRET_KEY`` je velmi důležité pro bezpečnost celé Django aplikace. Doporučujeme vygenerovat heslo pomocí příkazu

.. code-block:: console

    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

- Proměnnou ``GOOGLE_DOMAIN`` není nutné vyplňovat, ale bez jejího nastavení na doménu pro Google Workspace nebude fungovat synchronizace skupin.

- Proměnná ``FIO_TOKEN`` by měla obsahovat API token od Fio banky. Bez jejího korektního nastavení nebudou fungovat transakce.

- Proměnnou ``SQL_PASSWORD`` je vhodné rozumně nastavit, doporučujeme program ``pwgen``.

Hodnoty dalších proměnných nedoporučujeme bezdůvodně měnit.

Přesuneme se k proměnným PostgreSQL serveru. Upravíme obsah souboru ``.env_psql`` na

.. code-block:: console

    POSTGRES_USER=vzs
    POSTGRES_PASSWORD=
    POSTGRES_DB=vzs-clenska-sekce

- Proměnnou ``POSTGRES_PASSWORD`` nastavíme na stejnou hodnotu jako proměnnou ``SQL_PASSWORD`` ze souboru ``.env``

Poslední částí konfigurace je nastavení reverzní proxy Caddy. Soubor ``.env_caddy`` nastavíme na 

.. code-block:: console

    LOG_FILE=/data/access.log
    EMAIL=

Do proměnné ``EMAIL`` doplníme email, který chceme používat pro ACME challenge při získávání HTTPS certifikátu.

Posledním souborem ke konfiguraci je ``Caddyfile``, kde nastavíme reverzní proxy na naši doménu a server pro statické soubory. Obsah souboru ``Caddyfile`` upravíme na

.. code-block:: console

    is.vzs-praha15.cz:443 {
    tls admin@vzs-praha15.cz
        handle_path /static/* {
            root * /var/www/staticfiles
            file_server
        }
    reverse_proxy vzs-clenska-sekce-backend:8080
    }

První řádek obsahující doménu a druhý řádek obsahující email vhodně upravíme.

Poté můžeme sestavit docker image projektu.

.. code-block:: console

    ./docker-build.sh  (Linux)

    docker-build.bat  (Windows)

Projekt pro svoji funkčnost vyžaduje otevření pouze portu 80 a 443, je nutné zakázat přístup z Internetu zejména na port 5432 (PostgreSQL) a port 8080 (Gunicorn). Doporučujeme použít program ``ufw``.

Pomocí příkazu ``docker compose up`` je možné vytvořit kontejnery a spustit server.