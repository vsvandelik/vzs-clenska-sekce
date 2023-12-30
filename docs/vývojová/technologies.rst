.. _technologies:

***************************************
Využité technologie
***************************************

IS je standardní klient-server aplikací vytvořenou pomocí webového frameworku Django a dalších technologií, které uvedeme v této části.

---------------------
Python
---------------------
Python je vysokoúrovňový interpretovaný programovací jazyk, který byl poprvé vydán v roce 1991 nizozemským programátorem Guido van Rossumem. Python je známý pro svou jednoduchou syntaxi, srozumitelnost, díky čemuž je oblíbeným jazykem pro začátečníky i zkušené programátory. Python se používá v řadě různých aplikací, včetně vývoje webových stránek, vědeckých výpočtů, analýzy dat aj. V současné době se Python může chlubit velkou komunitu vývojářů a uživatelů, díky čemuž je k dispozici mnoho knihoven a nástrojů třetích stran, které rozšiřují jeho možnosti [1]_.

Python využíváme kvůli volbě frameworku Django, které je v Pythonu vytvořené.

.. [1] Zdroj: oficiální stránky Pythonu, odkaz: `<https://www.python.org>`_. 

---------------------
Django [2]_
---------------------

Django populární open-source webový framework vydaný pod svobodnou licencí BSD 3-Clause [3]_. postavený na programovacím jazyku Python. Poprvé byl uvolněn v roce 2005 s cílem zjednodušit proces vytváření webových aplikací. 

Jádrem Django je architektonický vzor MVC (model-view-controller), který pomáhá vytvářet udržovatelné webové aplikace. Django však svou implementaci tohoto vzoru označuje jako „model-view-template“ (MVT), kde vrstva šablony (angl. template) odděluje prezentační logiku od zbytku aplikace. 

Jednou z klíčových předností Django je důraz na rychlý vývoj a jednoduchost kódu. Dodržováním zásady DRY („Do Not Repeat Yourself“) podporuje Django psaní opakovatelně použitelného kódu, což vede ke zvýšení produktivity a snadnější údržbě aplikací v budoucnu. 

Django následuje filozofii Python a stejně jako jazyk samotný obsahuje bohatou sadu funkcí a vlastností již v základní instalaci. Jako příklad můžeme uvést ORM (Object-Relational Mapping) pro práci s databázemi. ORM poskytuje abstrakční vrstvu, která vývojářům umožňuje komunikovat s databází pomocí Python, aniž by bylo nutné psát vlastní dotazy SQL. Aktuálně Django oficiálně podporuje několik DB systémů, konkrétně: PostgreSQL, MariaDB, MySQL, Oracle, SQLite. 

U Django hraje významnou roli také jeho silný ekosystém. Má aktivní komunitu, která přispívá k jeho vývoji a udržuje mnoho rozšiřujících balíčků, díky kterým je možné např. použít ORM Django k připojení se i na MSSQL databázi.

Framework Django je nejdůležitější závislostí :term:`IS`.

.. [2] Zdroj: oficiální stránky Djanga, odkaz: `<https://www.djangoproject.com>`_. 
.. [3] BSD 3-Clause je svobodnou licencí pro open-source SW. Jedná se o jednu z nejrozšířenějších licencí používaných pro open-source SW. Znění licence viz `<https://opensource.org/license/bsd-3-clause>`_. 

---------------------
Bootstrap [4]_
---------------------
Bootstrap je populární framework pro tvorbu uživatelských rozhraní vydaný pod licencí MIT [5]_. Bootstrap zjednodušuje vývoj uživatelského rozhraní poskytováním předem navržených responzivních komponent a stylů.

Barvy, styly a některé komponenty Bootstrapu jsou použity na většině částí uživatelského rozhraní :term:`IS`, navíc šablona AdminLTE vyžaduje Bootstrap jako svoji závislost.

.. [4] Zdroj: oficiální stránky Bootstrapu, odkaz: `<https://getbootstrap.com>`_.
.. [5] MIT licence je svobodnou licencí pro open-source software. Původně byla vyvinuta a používána MIT (Messachusettským technologickým institutem), po kterém je i pojmenována. Znění licence viz `<https://opensource.org/license/mit>`_.


---------------------
AdminLTE [6]_
---------------------

AdminLTE je open-source šablona dostupná pod licencí MIT postavená na frameworku Bootstrap. Poskytuje řadu komponent uživatelského rozhraní, jako jsou grafy, tabulky, formuláře apod., které vývojářům pomáhají snadno a rychle vytvářet moderně vypadající responzivní webové aplikace. Nespornou výhodou je vysoká přizpůsobitelnost šablony, což vývojářům umožňuje upravit vzhled tak, aby odpovídal jejich specifické aplikaci. AdminLTE je mezi vývojáři oblíbená šablona a byla použita v řadě projektů. Jako příklad můžeme uvést ReCodEx, což je na MFF UK dobře známý systém pro analýzu a automatické vyhodnocování programátorských úloh.

AdminLTE poskytuje :term:`IS` moderně vypadající šablonu.

.. [6] Zdroj: oficiální stránky AdminLTE, odkaz: `<https://adminlte.io>`_.

---------------------
PostgreSQL [7]_
---------------------

PostgreSQL je open-source databázový systém vydaný pod svobodnou licencí, který klade důraz na rozšiřitelnost a shodu s SQL. Poprvé byl vydán v roce 1989 a nyní je jedním z nejrozšířenějších DB systémů používaných v současnosti.

PostgreSQL je vysoce škálovatelný a podporuje také replikační a clusterové použití, je proto vhodný pro použití v kritických aplikacích. Zásadní odlišností oproti některým konkurenčním DB systémům je silný důraz na dodržování standardů. Je plně kompatibilní se standardy SQL, což usnadňuje práci při migraci dat při použití různých DB systémů, které dodržují standard SQL.

.. [7] Zdroj: oficiální stránky PostgreSQL, odkaz: `<https://www.postgresql.org>`_.



---------------------
Cron [8]_
---------------------
Něco random o cronu.

.. [8] Zdroj: blabla