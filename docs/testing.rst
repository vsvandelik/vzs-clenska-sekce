##########################
Testování
##########################

Pro účely lepšího představaní zamýšleného použití a testování projektu jsme připravili fiktivní data, která rámcově odpovídají realitě. 

***************************************
Import dat
***************************************
Před importem dat je nutné mít sestavené funkční prostředí viz :doc:`./installation`. Poté je možné data naimportovat příkazem

.. code-block:: console

    python manage.py loaddata data/db.json

***************************************
Účty
***************************************
* Všechny hesla existujích účtů jsou nastavena na ``Heslo1234.``
* Výchozí administrátorský účet má email ``admin@vzs.cz``

***************************************
Nastavení času
***************************************
Některé úkony není možné provést pokud jiná akce neproběhla. Pro důkladné ověření funkcionality je zapotřebí přepsat aktuální čas. To je možné provést nastavením proměnné ``CURRENT_DATETIME`` v souboru ``.env`` na vhodný čas s časovým pásmem ve formátu ISO 8601. Na začátek můžeme doporučit nastavení ``CURRENT_DATETIME=2023-09-01T00:00:00+01:00``, kdy existují proběhlé i nadcházející události.