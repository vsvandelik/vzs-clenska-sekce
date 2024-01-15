##########################
Instalační dokumentace
##########################

V tomto dokumentu jsou detailně popsány všechny scénáře spouštění a nasazení projektu včetně produkčního nasazení.

V celém tomto dokumentu předpokládáme, že se v terminálu nacházíme v kořenovém adresáři projektu.

.. _local-debug:

***************************************
Lokální debug spuštění
***************************************
Lokální debug spuštění je vhodné, pokud nám stačí projekt spustit na lokálním prostředí. Je nutné si uvědomit, že při tomto spuštění je použit vestavěný webový server Djanga, který není určen pro produkční nasazení a SQLite, jehož použití není optimální při paralelních přístupech.

--------------------------------------
Upozornění
--------------------------------------
Při :ref:`local-debug` můžete narazit na dva nedostatky.

1. Abecední řazení neodpovídá českým konvencím. To je způsobeno použití SQLite databáze, která řadí znaky dle pořadí definované v UTF-8.
2. Select2 widgety mohou být pomalejší. To je způsobeno neexistencí cache, která je vyžadována balíčkem :ref:`django-select2`.

Tyto nedostatky nejsou přítomné v produkčním prostředí (:ref:`local-production`, :ref:`production`), kde se používá PostgreSQL jako databázový server a Redis pro implementaci cache.

Dále nedoporučujeme provádět SQL operace nad obrovským počtem dat, tyto operace jsou řádově pomalejší při použití SQLite oproti databázovým serverům, které jsou určené pro produkční prostředí a zvládají paralelní přístupy.

-------------------
Prerekvizity
-------------------
- Python ≥ 3.11 
- Node.js ≥ 17.0.0

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

    npm install
    pip install -r requirements.txt

5. Spustíme migrace

.. code-block:: console

    python ./manage.py migrate

Nyní je možné spustit webový server Djanga.

.. code-block:: console

     python ./manage.py runserver 8080


.. _local-production:
***************************************
Lokální test produkčního nasazení
***************************************
Tento druh spuštění je vhodný v případě, kdy chceme otestovat funkčnost projektu při použití všech částí produkčního nasazení (Gunicorn, PostgreSQL, Caddy, Redis) vyjma HTTPS.


-------------------
Prerekvizity
-------------------
- docker ≥ 1.13.1


Před vytvořením docker image je nutné provést konfiguraci.

1. Překopírujeme soubor ``.env.dist`` do ``.env`` a provedeme nastavení proměnných dle nápovědy u každé proměnné. Doporučujeme vycházet z následujícího nastavení proměnných, pokud jiné hodnoty nejsou k dispozici.

.. code-block:: console

    DEBUG=True
    SECRET_KEY=django-insecure
    GOOGLE_DOMAIN=
    FIO_TOKEN=

    REDIS_ENABLE=True
    REDIS_LOCATION=redis://redis:6379/2
    REDIS_PASSWORD=secret-password

    SQL_ENGINE=django.db.backends.postgresql
    SQL_DATABASE=vzs-clenska-sekce
    SQL_USER=vzs
    SQL_PASSWORD=supersecret
    SQL_HOST=db
    SQL_PORT=5432

2. Nastavíme proměnné o stejných hodnotách i z pohledu PostgreSQL. Soubor ``docker/.env_psql`` by měl vypadat takto

.. code-block:: console

    POSTGRES_USER=vzs
    POSTGRES_PASSWORD=supersecret
    POSTGRES_DB=vzs-clenska-sekce

3. Nastavíme proměnné o stejných hodnotách i z pohledu Redis. Soubor ``docker/.env_redis`` by měl vypadat takto

.. code-block:: console

    REDIS_PASSWORD=secret-password


4. Nastavíme konfigurační soubor ``docker/Caddyfile`` pro reverzní proxy Caddy

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

    ./docker/docker-build.sh  (Linux)

    docker\docker-build.bat  (Windows)


Nyní můžeme celý projekt spustit jedním příkazem, nutné spouštět z adresáře docker.

.. code-block:: console

    docker compose up

.. _production:

***************************************
Produkční nasazení
***************************************
Zde si popíšeme, co všechno je potřeba udělat, abychom mohli projekt bezpečně vystavit na Internet.

-------------------
Prerekvizity
-------------------
- docker ≥ 1.13.1

Nejprve se pustíme do konfigurace. Nahradíme obsah souboru ``.env`` obsahem ze souboru ``.env.dist`` doplníme zbylé nevyplněné proměnné.

.. code-block:: console

    DEBUG=False
    SECRET_KEY=
    GOOGLE_DOMAIN=
    FIO_TOKEN=
    REDIS_ENABLE=True
    REDIS_LOCATION=redis://redis:6379/2
    REDIS_PASSWORD=
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

- Do proměnných ``REDIS_PASSWORD`` a ``SQL_PASSWORD`` je vhodné nastavit rozumně silné heslo, doporučujeme použít program ``pwgen``.

Hodnoty dalších proměnných nedoporučujeme bezdůvodně měnit.

Přesuneme se k proměnným PostgreSQL serveru. Upravíme obsah souboru ``docker/.env_psql`` na

.. code-block:: console

    POSTGRES_USER=vzs
    POSTGRES_PASSWORD=
    POSTGRES_DB=vzs-clenska-sekce

- Proměnnou ``POSTGRES_PASSWORD`` nastavíme na stejnou hodnotu jako proměnnou ``SQL_PASSWORD`` ze souboru ``.env``

Dále upravíme soubor ``docker/.env_redis``, kde nastavíme proměnnou ``REDIS_PASSWORD`` na stejnou hodnotu jako proměnnou stejného jména ze souboru ``.env``

Poslední částí konfigurace je nastavení reverzní proxy Caddy. Soubor ``docker/.env_caddy`` nastavíme na 

.. code-block:: console

    LOG_FILE=/data/access.log
    EMAIL=

Do proměnné ``EMAIL`` doplníme email, který chceme používat jako výchozí pro ACME challenge při získávání HTTPS certifikátu.

Posledním souborem ke konfiguraci je ``docker/Caddyfile``, kde nastavíme reverzní proxy na naši doménu a server pro statické soubory. Obsah souboru ``docker/Caddyfile`` upravíme na

.. code-block:: console

    is.vzs-praha15.cz:443 {
    tls admin@vzs-praha15.cz
        handle_path /static/* {
            root * /var/www/staticfiles
            file_server
        }
    reverse_proxy vzs-clenska-sekce-backend:8080
    }

První řádek obsahující doménu a druhý řádek obsahující email vhodně upravíme, email můžeme vynechat, pokud máme definovanou proměnnou ``EMAIL`` v ``docker/.env_caddy``.

Poté můžeme sestavit docker image projektu.

.. code-block:: console

    ./docker/docker-build.sh  (Linux)

    docker\docker-build.bat  (Windows)

Projekt pro svoji funkčnost vyžaduje otevření pouze portu 80 a 443, je nutné zakázat přístup z Internetu zejména na port 5432 (PostgreSQL), 8080 (Gunicorn) a 6379 (Redis). Doporučujeme použít program ``ufw``.

Pomocí příkazu ``docker compose up`` z adresáře docker je možné vytvořit kontejnery a spustit server.