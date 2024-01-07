.. _testing:

##########################
Testování
##########################

Pro účely lepšího představení zamýšleného použití a testování projektu jsme připravili fiktivní data, která rámcově odpovídají realitě. 

***************************************
Import dat
***************************************
Před importem dat je nutné mít sestavené funkční prostředí viz :doc:`../instalační/installation`. Poté je možné data naimportovat spuštěním skriptu

.. code-block:: console

    data\db-restore.bat  (Windows)

    ./data/db-restore.sh  (Linux)

Pokud byste pro testování chtěli používat docker, namísto ``db-restore`` skriptů jsou připravené ``db-restore-to-docker`` skripty pro Windows i Shell. Analogicky pro zálohu dat existují skripty ``db-backup`` a ``db-backup-from-docker``.

***************************************
Popis testovacích dat
***************************************
Při vytváření testovacích dat někdy došlo k odlišení se od reality pro účely demonstrace funkcionality. Je nutné brát v potaz, že dostupná funkcionalita se liší v závislosti na datech a časech vyplněných položek v :term:`IS` a systémovém aktuálním datu a času. Z těchto důvodu je možné ručně nastavit systémový čas environmentální proměnnou ``CURRENT_DATETIME`` v souboru ``.env`` s časovým pásmem ve formátu ISO 8601. Pro začátek můžeme doporučit nastavení ``CURRENT_DATETIME=2023-11-15T00:00:00+01:00``. Při neopatrném nastavení času do minulosti můžeme dostat systém do stavu, kdy budou existovat uzavřené a zpracované události, které by měly proběhnou v budoucnu. Při tomto nastavení může :term:`IS` vykazovat známky nedefinovaného chování, protože při standardním použití se do tohoto stavu nikdy nemůže dostat.

--------------------------
Administrátor
--------------------------
Na výchozí administrátorský účet je možné se přihlásit pomocí

- email: ``admin@vzs.cz``
- heslo: ``Heslo1234.``

----------------------------------------------------
Přihlášení jako neadministrující osoba
----------------------------------------------------
Některé zajímavé osoby, které se účastní několika událostí jsou spravovány přímo Adminem VZS (``admin@vzs.cz``), to znamená, že po přihlášení se na účet ``admin@vzs.cz`` je možné v pravém horním rohu překliknout účet na spravovanou osobu.

Pokud se chceme přihlásit na jinou osobu, musíme přes účet ``admin@vzs.cz`` přejít na Seznam osob a vybrat si konkrétní osobu, u které na kartě ``Uživatelský účet`` je možné vidět, zda má osoba zpřístupněný uživatelský účet (zda má účet heslo). Pokud účet nemá heslo, stačí nové heslo nastavit a poté je možné se přihlásit. V případě, že účet již existuje, tak je možné použít heslo ``Heslo1234.``, které mají stejně jako administrátor nastavené a všechny zpřístupněné účty, případně je možné tlačítkem "Vygenerovat nové heslo" získat heslo nové.

----------------------------------------------------
Další doporučené nastavení systémového času
----------------------------------------------------
Při použití výchozího doporučovaného nastavení ``CURRENT_DATETIME=2023-11-15T00:00:00+01:00`` jsou typy jednorázových událostí včetně jejich stavu zhruba ve stejném zastoupení. Pokud bychom si chtěli vyzkoušet uzavřít událost, můžeme si tuto funkcionalitu vyzkoušet na události ``Den s Ajaxem - prezentačka - Štětí``. Pokud bychom si však chtěli zkusit uzavřít kurz, zjistíme, že nejbližší kurz se koná 18-19.11.2023 a tudíž ho není možné uzavřít. V tomto případě je možné upravit datum a čas na např. ``CURRENT_DATETIME=2023-11-20T00:00:00+01:00``, který nezpůsobí nekonzistenci, protože se jedná o posunutí času do budoucnosti. 

----------------------------------------------------
Testování tréninků
----------------------------------------------------
U tréninků vytvořená testovací data rámcově reflektují skutečnou strukturu tréninků. Vzhledem k množství reálných dat, jsme se rozhodli, že se omezíme pouze na tréninky ``plavecký trénink 8-13 let skup. 1 Hostivař`` a ``plavecký trénink 8-13 let skup. 2 Hostivař``, kde jsme vyplnili osoby a docházku několik prvních konání tréninku.

Při testování se doporučujeme zaměřit na osoby ``Jan Beneš``, ``Andrea Horáková`` a ``Jana Marečková``.
