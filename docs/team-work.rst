##########################
Práce v týmu
##########################

Práce v týmu započala dle specifikace, brzy jsme ovšem zjistili, že dělení na původní 3 Django aplikace je příliš hrubé a přistoupili jsme k jemnějšímu dělení na konečných 12 aplikací. Každý člen týmu namísto garantování 1 aplikace garantoval zhruba 4 aplikace. Veškeré změny procházeli skrze code review jiného člena týmu (obvykle přiděleného reviewera).

Během vývoje se ukázala potřeba použít Github Actions [1]_ pro automatickou kontrolu běhu migrací, automatický deployment dokumentace na GitHub Pages [2]_ apod.

Při dokončování projektu se pečlivě rozplánovali zbývající týdny a rozdělila se práce mezi jednotlivé členy týmu dle jejich časových možností.

.. [1] GitHub Actions slouží k automatizaci běžných postupů a ke kontinuální integraci. Více info viz `<https://github.com/features/actions>`_

.. [2] GitHub Pages jsou webhostingovou službou. Umožňují hostovat statické webové stránky přímo z GitHubu. Více info viz `<https://pages.github.com/>`_