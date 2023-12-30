.. _front-end:
***************************************
Front-end
***************************************
Jak již bylo zmíněno v kapitole :ref:`architektura`, základním součástí renderování HTML dokumentů je šablonovací engine Jinja, který používá každý nestatický HTML dokument pro renderování výsledného HTML kódu, který se zobrazí uživateli. Pro zlepšení UX a zvýšení komfortu při používání aplikace bylo použito několik dalších více či méně standardních knihoven a frameworků.

----------------------------------------
Bootstrap
----------------------------------------
Zásadním front-endovým frameworkem, který byl použit je Bootstrap. Použití Bootstrapu na jedné straně spočítá v tom, že hlavní šablona :ref:`admin-lte` ho vyžaduje jako svoji závislost. Na druhé straně Bootstrap definuje lépe vypadající výchozí verzi téměř každé existující komponenty. Bez předchozího vzdělání v oblasti UX je velmi obtížné a časově náročné dosáhnout podobných kvalit, proto je Bootstrap použit téměř ve všech komponentách všech HTML šablon.

Jako příklad použití Bootstrapu uvedeme použití modálního okna. Modální okno se používá při mazání komplexnějších objektů pro potvrzení smazání (např. mazání organizátorských pozic). Obsah zprávy o potvrzení smazání objektu však závisí na konkrétním objektu, který chceme smazat. Tento problém je řešen kombinací Javascriptu, který pošle GET požadavek, jehož odpoveď se zobrazí uvnitř modálního okna.

.. _admin-lte:
----------------------------------------
AdminLTE
----------------------------------------


----------------------------------------
jQuery
----------------------------------------

----------------------------------------
DataTables
----------------------------------------

----------------------------------------
Select2
----------------------------------------

----------------------------------------
FontAwesome
----------------------------------------
