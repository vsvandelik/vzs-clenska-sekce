.. _architektura:

***************************************
Architektura
***************************************
:term:`IS` je vytvořen jako monolitická MVC aplikace, která se skládá z back-endu a front-endu. Back-end využívá framework Django, front-end využívá šablonovací nástroj Jinja a další populární knihovny viz :ref:`technologies`.


---------------------
Back-end
---------------------
Framework Django je velice komplexní framework, který definuje řadu konvencí, které určují, jak by se framework měl používat. Jako příklad můžeme uvést např. rozdělení do Django aplikací a přesně daná struktura každé aplikace. Při vývoji jsme se snažili o maximální možné dodržení konvencí Djanga. V budoucím vývoji doporučujeme se těchto konvencí držet taktéž, protože bez jejich dodržování ztrácí použití Djanga svoje výhody oproti konkurenčním frameworkům. Navíc se kód stane značně nepřehledným pro osoby, které mají s vývojem aplikací v Djangu zkušenosti.

Back-end se dělí na 12 Django aplikací.

- :ref:`api`
- :ref:`events`
- :ref:`groups`
- :ref:`features`
- :ref:`one_time_events`
- :ref:`pages`
- :ref:`persons`
- :ref:`positions`
- :ref:`trainings`
- :ref:`transactions`
- :ref:`users`
- :ref:`vzs`

Po kliknutí na název aplikace se zobrazí detailnější popis vybrané aplikace.

Každá z těchto aplikací řeší samostatný, dobře definovaný celek, který je patrný z názvu aplikace. Např. aplikace transactions sdružuje veškerou implementaci týkající se transakcí, které se mohou uvnitř :term:`IS` provádět. Aplikace mezi sebou komunikují a většinou sdružují všechny URL cesty pod společný základ, např. všechny URL cesty aplikace trainings začínají ``treninky/``. Toto neplatí např. pro aplikaci features, kde vlastnosti mohou být jedním ze tří druhů, proto aplikace využívá tři URL cesty ``kvalifikace/``, ``opravneni/``, ``vybaveni/``.

---------------------
Front-end
---------------------
Front-end je do určité míry spjatý s back-endem, protože používá standardní šablonovací nástroj Djanga – Jinja pro vykreslování HTML dokumentů. Hlavní šablona se vyskytuje se na každé stránce :term:`IS` a pochází z AdminLTE. Pro vytváření jednotlivých specifických komponent na stránkách se hojně používá Bootstrap. Vyjmenujme alespoň často používané Bootstrap Cards nebo třídu "btn" a barvy "primary", "secondary".

Další informace o front-endu se nachází na zvláštní stránce :ref:`front-end`.

---------------------
Databáze
---------------------
O komunikaci s databází se stará Django ORM (objektové relační mapování), díky kterému nemusíme psát ručně SQL dotazy a kontrolovat kompatibilitu napříč DB systémy. Při :ref:`Lokálním debug spuštění <local-debug>` se standardně používá SQLite databáze, při :ref:`Produkčním nasazení <production>` se používá PostgreSQL.

Další informace o databázi se nachází na zvláštní stránce :ref:`db`.