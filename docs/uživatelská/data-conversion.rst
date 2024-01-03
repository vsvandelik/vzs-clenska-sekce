***************************************
Převod dat ze starého systému
***************************************

Nový systém obsahuje utilitu na převod dat ze starého systému, který běží na adrese
https://clen.vzs-praha15.cz. V rámci převodu dat se převádějí pouze informace
o osobách a jejich uživatelských účtech. Zbytek dat (především informace
o trénincích, jiná data aktuální systém nemá) je natolik odlišný, že automatický
převod není možný.

Z důvodu větší kontroly nad přenášenými daty je převod připraven tak, že
se pomocí speciálního nástroje v rámci :term:`IS` vytvoří soubor s daty novými, který lze po důkladné manuální kontrole nahrát do databáze nového systému.

---------------------
Postup převodu
---------------------

1. Z databáze starého systému stáhněte tabulku `uzivatel` ve formátu CSV. Kódování zvolte
   UTF-8 a jako oddělovač znaků použijte symbol čárky (,).

2. Spustťe konverzní skript:

.. code-block:: console

   python manage.py convert_old_system_data cesta_k_souboru.csv > person.json

3. Opravte chyby na které upozorní konverzní skript na chybovém výstupu. Opakujte kroky
   2 a 3 dokud skript nevytvoří soubor s daty bez chyb. Více o chybách najdete v :ref:`popis_nejcastejsich_chyb`.

5. Překontrolujte si výsledný soubor ``person.json``.

4. Pomocí nástroje ``loaddata`` zabudovaného přímo ve frameworku Django nahrajte data do databáze
   nového systému:

.. code-block:: console

   python manage.py loaddata person.json

---------------------
Popis převáděných dat
---------------------

Zde pro přehlednost uvádíme tabulku sloupců z tabulky `uzivatel` starého systému s informací,
jestli jsou či nejsou přenášeny do výstupního souboru.

.. csv-table:: Převáděné sloupce
   :file: data-conversion-columns-table.csv
   :widths: 30, 20, 50
   :header-rows: 1

.. _popis_nejcastejsich_chyb:

------------------------
Popis nejčastějších chyb
------------------------

Typická chybová hláška vypadá následovně:

.. code-block:: console

    Error in line 4: health_insurance_company: Hodnota 'VZS - ZPP' není platná možnost.

Z hlášky se tedy můžeme dozvědět jednak, na jakém řádku je problém a jednak, s kterým
polem je problém.

- ``health_insurance_company: Hodnota 'XXX' není platná možnost.`` - je třeba zadat buď číslo české
  pojišťovny či její kód
- ``health_insurance_company: Two different health insurance companies: XXX and YYY`` - v obou sloupcích
  se zdravotní pojišťovnou je validní hodnota a není tedy jasné, jakou zvolit
- ``email: E-mailová adresa XXX již byla použita u osoby s jiným jménem (XXX). Osoba se vynechává.`` - je třeba
  opravit či odebrat e-mailovou adresu, protože již existuje osoba s touto e-mailovou adresou, pozor, že
  adresa musí být jedinečná napříč všemi osobami i rodiči
- ``email: Vložte platnou e-mailovou adresu.`` - e-mailová adresa není ve správném formátu
- ``time data '1/4/2011' does not match format '%d.%m.%Y'`` - datum je ve špatném formátu, je třeba jej
  převést do formátu ``DD.MM.RRRR``
