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
Šablona s levým postranním menu, kterou zahrnují všechny HTML soubory :term:`IS`, je součástí AdminLTE. Šablona byla zvolena pro svůj jednotný vzhled při použití Bootstrapu a jednoduché použití.

----------------------------------------
jQuery
----------------------------------------
Hlavním důvodem pro použití jQuery byl důvod, že jej vyžadují další komponenty, které jsme chtěli použít (:ref:`DataTables`, :ref:`Select2`). Postupem času se ukázalo, že pro některé části Javascriptu se použití jQuery ukázalo jako adekvátní, protože značně zjednodušilo kód.

Momentálně je aplikována konvence, že není nutné vždy používat jQuery, pokud existuje ve standardním Javascriptu odpovídající ekvivalentní způsob, jak dosáhnout stejné funkcionality. Pokud však je kód pomocí jQuery jednodušší a srozumitelnější, je jeho použití preferované. Rozhodli jsme se tak proto, že řada knihoven a frameworků ustupuje od používání jQuery, např. AdminLTE od verze 5 již nezávisí na jQuery. Dá se předpokládat, že tento trend bude pokračovat a další součásti již nebudou vyžadovat jQuery. V budoucnu je možné, že dojde k odstranění jQuery jako závislosti projektu.

.. _DataTables:

----------------------------------------
DataTables
----------------------------------------

.. _Select2:

----------------------------------------
Select2
----------------------------------------

----------------------------------------
FontAwesome
----------------------------------------
