***************************************
Autentizace
***************************************

:term:`IS` používá pro autentizaci standardní nástroje Djanga
s drobným přizpůsobením. V této stránce je popsán základní přehled fungování
těchto nástrojů a všechna přizpůsobení. Rovněž je zde popsáno, jak se dá
systém rozšířit.

-----
Model
-----
Základní uživatelský model poskytnutý Djangem je značně změněn.
Model obsahuje pouze šifrované heslo a foreign key na osobu, který je zároveň primary key.
Při autentizaci uživatele se používá e-mail, který je obsažen v modelu osoby,
jakož i všechny ostatní údaje o dané osobě.

--------
Backendy
--------

Django poskytuje ve svém autentizačním frameworku koncept backendů.
Na začátku autentizace uživatele se posbírají potřebné parametry,
podle kterých je možné identifikovat a autentizovat uživatele.
Entita, která zajistí tuto identifikaci a autentizaci se nazývá backend.
Proces úspěšné autentizace vrací instanci uživatele.

:term:`IS` používá dva backendy. Jeden ověřuje na základě e-mailu a hesla,
druhý na základě Google OAuth2 protokolu.

``PasswordBackend``
^^^^^^^^^^^^^^^^^^^
::

    user = authenticate(request, email=email, password=password)

Tento backend dědí téměř veškeré chování od ``ModelBackend``.
Jediným rozdílem je, že standardní ``ModelBackend`` ověřuje pouze na základě polí
uživatelského modelu, zatímco ``PasswordBackend`` ověřuje také na základě e-mailu,
který je obsažen v modelu osoby.
Před autentizací tedy musí získat instanci osoby podle e-mailu.

``GoogleBackend``
^^^^^^^^^^^^^^^^^
::

    user = authenticate(request, code=code)

Tento backend autentizuje uživatele na základě tokenu,
který je zaslán v GET requestu od Google autentizačního serveru.

Používá knihovny `google-auth <https://google-auth.readthedocs.io/en/latest/>`
a `google-auth-oauthlib <https://google-auth-oauthlib.readthedocs.io/en/latest/>`.

Postup celé autentizace je následující:

1.  View, který zpracovává požadavek uživatele na přihlášení pomocí Google,
    přesměruje na Google autentizační stránku. Té je nutné zadat url,
    na kterou chceme dostat odpověď. Tato url musí být zaregistrována
    v Google konzole jako povolena. Také je možné v query parametru ``state``
    prodat libovolný řetězec. Ten dostaneme v odpovědi od autentizačního serveru.

2.  Uživatel se přihlásí na Google autentizační stránce a ta jej přesměruje
    na url, kterou jsme zadali v předchozím kroku.
    
3.  View, který zpracovává odpověď, obdrží GET request s query parametrem ``code``,
    což je autentizační token. Také dostane query parametr ``state``,
    kde je nezměněný řetězec, který jsme poslali v prvním kroku.
    Token se použije k autentizaci uživatele na Google serveru.
    Tato autentizace vrátí informace o uživateli - zejména e-mail.
    Úspěšná Google autentizace v kombinaci s uživatelským účtem
    pro osobu s daným e-mailem znamená,
    že uživatel je podle tohoto backendu autentizován.

:term:`IS` používá při nepovoleném přístupu na stránku, která vyžaduje přihlášení,
přesměrování na původní stránku pomocí použití
``next`` query parametru v login stránce.
Aby bylo možné přesměrovat na správnou stránku i při použití Google autentizace,
je tento parametr zakódován do ``state`` query parametru.
