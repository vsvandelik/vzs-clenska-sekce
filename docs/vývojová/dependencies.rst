**************************
Další závislosti
**************************
Na této stránce popíšeme další závislosti :term:`IS`. Nebudeme se zde zabývat závislostmi, které rozšiřují funkce Djanga – ty jsou popsány na stránce :doc:`./django-extensions`.

.. _dependencies_from_requirements.txt:

-------------------------------------------------
Závislosti definované v souboru requirements.txt
-------------------------------------------------
Zde jsou obsaženy závislosti, které je nutné mít vždy nainstalované. Konkrétně se jedná o:

- :ref:`crispy-bootstrap4`
- :ref:`fiobank`
- :ref:`google-api-python-client <google_balicky>`
- :ref:`google-auth <google_balicky>`
- :ref:`google-auth-httplib2 <google_balicky>`
- :ref:`google-auth-oauthlib <google_balicky>`
- :ref:`python-dateutil`

.. _crispy-bootstrap4:

crispy-bootstrap4
^^^^^^^^^^^^^^^^^^
Jedná se o extension balíčku :ref:`django-crispy-forms` umožňující nastavení ``CRISPY_TEMPLATE_PACK = "bootstrap4"`` při kterém se používá Bootstrap 4.

.. _fiobank:

fiobank
^^^^^^^^
Tento balíček umožňuje zasílat a kontrolovat platby na bankovním účtu :term:`Organizace`.

.. _google_balicky:

google-api-python-client, google-auth, google-auth-httplib2, google-auth-oauthlib
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Tyto balíčky umožňují přihlašování do :term:`IS` pomocí Google účtu a synchronizaci skupin s Google Workspace.

.. _python-dateutil:

python-dateutil
^^^^^^^^^^^^^^^^
python-dateutil přináší pokročilejší funkce pro práci s daty a časy. :term:`IS` konkrétně používá funkci ``relativedelta`` pro vymezení relativní lhůty splatnosti. 


.. _dependencies_from_requirements_dev.txt:

-----------------------------------------------------
Závislosti definované v souboru requirements_dev.txt
-----------------------------------------------------
Zde jsou obsaženy závislosti, které nejsou nutné pro spuštění projektu, ale jsou povinné pro vývoj. Konkrétně se jedná o:

- :ref:`Genderize`
- :ref:`pre-commit`
- :ref:`rinohtype`
- :ref:`sphinx`

.. _Genderize:

Genderize
^^^^^^^^^^
Balíček implementující API služby `<https://genderize.io>`_, která na základě křestního jména predikuje pohlaví osoby. V případě platného předplatného k této službě, je možné tuto funkcionalitu využít při převodu dat ze starého systému. Pro více informací o převodu dat ze starého systému navštivte stránku :doc:`../uživatelská/data-conversion`.

.. _pre-commit:

pre-commit
^^^^^^^^^^^
Framework pre-commit spouští nadefinované hooks před provedením příkazu ``git commit``. :term:`IS` využívá 2 hooks, které zajistí formátování kódu. Více informací o workflow viz :doc:`./contribute`.

.. _rinohtype:

rinohtype
^^^^^^^^^^^
rinohtype slouží ke zpracování dokumentů. Jeho výstupem jsou dokumenty ve formátu PDF. :term:`IS` tento balíček používá pro export dokumentace z reStructuredText souborů dokumentačního nástroje :ref:`sphinx` do PDF.

.. _sphinx:

sphinx
^^^^^^^^^^^
sphinx je univerzální nástroj pro vytváření dokumentace určený především pro projekty vytvořené v Pythonu. Tato dokumentace je napsána v reStructuredText souborech za pomocí nástroje sphinx, který do dokumentace navíc přidá anotace z kódu.

.. _dependencies_from_requirements_prod.txt:

-----------------------------------------------------
Závislosti definované v souboru requirements_prod.txt
-----------------------------------------------------
Zde jsou obsaženy závislosti, které jsou vyžadovány pouze pro běh v produkčním prostředí. Konkrétně se jedná o:

- :ref:`gunicorn`
- :ref:`psycopg2-binary`

.. _gunicorn:

gunicorn
^^^^^^^^^
HTTP server pro běh WSGI aplikací vhodný pro použití v produkčním prostředí. Při běhu v produkci :term:`IS` používá tento server v kombinaci s reverse proxy.

.. _psycopg2-binary:

psycopg2-binary
^^^^^^^^^^^^^^^^
Databázový ovladač, který Django využívá při použití PostgreSQL jako databázového serveru. Při běhu v produkci :term:`IS` nepoužívá SQLite ale právě PostgreSQL.