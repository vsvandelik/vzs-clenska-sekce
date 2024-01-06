.. _front-end:

***************************************
Front-end
***************************************
Jak již bylo zmíněno v kapitole :ref:`architektura`, základním součástí renderování HTML dokumentů je šablonovací engine Jinja, který používá každý nestatický HTML dokument pro renderování výsledného HTML kódu, který se zobrazí uživateli. Pro zlepšení UX a zvýšení komfortu při používání aplikace bylo použito několik dalších více či méně standardních knihoven a frameworků.

----------------------------------------
Bootstrap
----------------------------------------
Zásadním front-endovým frameworkem, který byl použit je Bootstrap. Použití Bootstrapu na jedné straně spočívá v tom, že hlavní šablona :ref:`admin-lte` ho vyžaduje jako svoji závislost. Na druhé straně Bootstrap definuje lépe vypadající výchozí verzi téměř každé existující komponenty. Bez předchozího vzdělání v oblasti UX je velmi obtížné a časově náročné dosáhnout podobných kvalit, proto je Bootstrap použit téměř ve všech komponentách všech HTML šablon. Při vytváření nových šablon je doporučeno používat Bootstrap v maximální možné míře.

Jako příklad použití Bootstrapu uvedeme použití modálního okna. Modální okno se používá při mazání komplexnějších objektů pro potvrzení smazání (např. mazání organizátorských pozic). Obsah zprávy o potvrzení smazání objektu však závisí na konkrétním objektu, který chceme smazat. Tento problém je řešen kombinací Javascriptu, který pošle GET požadavek, jehož odpoveď se zobrazí uvnitř modálního okna.

:ref:`Příklady použití modálních oken Bootstrapu. <Bootstrap_modals_example>`


.. _admin-lte:

----------------------------------------
AdminLTE
----------------------------------------
Šablona s levým postranním menu, kterou zahrnují všechny HTML soubory :term:`IS`, je součástí AdminLTE. Šablona byla zvolena pro svůj jednotný vzhled při použití Bootstrapu a jednoduché použití.

----------------------------------------
jQuery
----------------------------------------
Hlavním důvodem pro použití jQuery bylo, že jej vyžadují další komponenty, které jsme chtěli použít (:ref:`DataTables`, :ref:`Select2`). Postupem času se ukázalo, že pro některé části Javascriptu se použití jQuery ukázalo jako adekvátní, protože značně zjednodušilo kód.

Momentálně je aplikována konvence, že není nutné vždy používat jQuery, pokud existuje ve standardním Javascriptu odpovídající ekvivalentní způsob, jak dosáhnout stejné funkcionality. Pokud však je kód pomocí jQuery jednodušší a srozumitelnější, je jeho použití preferované. Rozhodli jsme se tak proto, že řada knihoven a frameworků ustupuje od používání jQuery, např. AdminLTE od verze 5 již není závislé na jQuery. Dá se předpokládat, že tento trend bude pokračovat a další součásti již nebudou vyžadovat jQuery. V budoucnu je možné, že dojde k odstranění jQuery jako závislosti projektu.

.. _DataTables:

----------------------------------------
DataTables
----------------------------------------
DataTables je knihovna vytvořenou pomocí jQuery, která vylepšuje tabulky. Tabulky získají funkce jako např. seřazení dle sloupce, zobrazení počtu řádků na stránku, hledání apod. Většina tabulek :term:`IS` využívá DataTables s různou úrovní konfigurace. Některé komplexní tabulky jako např. Seznam všech osob mají povolené všechny funkce DataTables, jednodušší a méně objemné tabulky jako např. Seznam organizátorských pozic jednorázové události mají povolené pouze řazení dle sloupce a ostatní funkce vypnuté.

Při návrhu nové tabulky, je nutné si rozmyslet očekávaný objem dat, který tabulka bude zobrazovat a zvážit jak DataTables pro zobrazení tabulky nakonfigurovat.

:ref:`Příklady použití DataTables. <DataTable_example>`


.. _Select2:

----------------------------------------
Select2
----------------------------------------
Select2 je další knihovna pro jQuery. Její význam spočívá ve vylepšení prvků ``<select>`` (select boxy). Tato knihovna se mezi závislosti :term:`IS` dostala až později. S přibývajícími daty jsme zjistili, že v některých select boxech by se při použití výchozích stylů špatně vyhledávalo. Vylepšení select boxů při použití Select2 spočívá v zobrazení vyhledávacího pole, které je pro řadu select boxů vhodné, např. select box pro výběr osoby se seznamu. Na druhou stranu :term:`IS` obsahuje i select boxy, kde dochází k výběru z malého množství položek, např. pohlaví, kde knihovna Select2 není používána.

Při návrhu nového select boxu doporučuje používat Select2 pouze pro select boxy, kde dochází k výběru z mnoha položek a konkrétní položku je rychlejší najít pomocí vyhledávacího pole.

:ref:`Příklady použití Select2. <Select2_example>`

----------------------------------------
FontAwesome
----------------------------------------
Pro účely zobrazení symbolů jsou používány ikonky z projektu FontAwesome. Zásadní výhodou oproti použití Unicode symbolů je garance, že FontAwesome ikonky vypadají na všech platformách stejně. Z těchto důvodu je doporučeno vždy upřednostit FontAwesome ikonku a pokud možno nepoužívat Unicode symboly.
