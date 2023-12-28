***************************************
Architektura
***************************************
:term:`IS` je vytvořen jako monolitická MVC aplikace, která se skládá z back-endu a front-endu. Back-end využívá framework Django, frontend využívá šablonovací nástroj Jinja a další populární knihovny viz :ref:`technologies`.


---------------------
Back-end
---------------------
Framework Django je velice komplexní framework, který definuje řadu konvencí, které určují jak by se framework měl používat. Jako příklad můžeme úvést např. rozdělení do Django aplikací a přesně daná struktura každé aplikace. Při vývoji jsme se snažili o maximální možné dodržení konvencí Djanga. V budoucím vývoji doporučujeme se těchto konvencí držet taktéž, protože bez jejich dodržování ztrácí použití Djanga svoje výhody oproti konkurenčním frameworkům. Navíc se kód stane značně nepřehledným pro osoby, které mají s vývojem aplikací v Djangu zkušenosti.

Back-end se dělí na 12 Django aplikací.

- api
- events
- groups
- features
- one_time_events
- pages
- persons
- positions
- trainings
- transactions
- users
- vzs

Po kliknutí na název aplikace se zobrazí detailnější popis vybrané aplikace.

Každá z těchto aplikací řeší samostatný, dobře definovaný celek, který je patrný z názvu aplikace. Např. aplikace transactions sdružuje veškerou implementaci týkající se tranksakcí, které se mohou uvnitř :term:`IS` provádět. Aplikace mezi sebou komunikují a sdružují všechny URL cesty pod společný základ, např. všechny URL cesty aplikace trainings začínají ``udalost/treninky/``. Toto neplatí pouze pro aplikaci features, kde vlastnosti mohou být jedním ze tří druhů, proto aplikace využívá tři URL cesty ``kvalifikace/``, ``opravneni/``, ``vybaveni/``.

---------------------
Front-end
---------------------
Front-end je do určité míry spjatý s back-endem, protože používá standardní šablonovací nástroj Djanga – Jinja pro renderování HTML dokumentů. Hlavní šablona se vyskytuje se na každé stránce :term:`IS` a pochází z AdminLTE. Pro vytváření jednotlivých specifických komponent na stránkách se hojně používá Bootstrap. Vyjmenujme alespoň často používané Bootstrap Cards nebo třídu "btn" a barvy "primary", "secondary". 

Další informace o front-endu se nachází na zvláštní stránce :ref:`front-end`.

---------------------
Databáze
---------------------
O komunikaci s databází se stará Django ORM (objektové relační mapování), díky kterému se nemusíme psát ručně SQL dotazy a kontrolovat kompatibility napříč DB systémy. Při :ref:`Lokálním debug spuštění <local-debug>` se standardně používá SQLite databáze, při :ref:`Produkčním nasazení <production>` se používá PostgreSQL.

Další informace o databázi se nachází na zvláštní stránce :ref:`db`.