##########################
Práce v týmu
##########################

Týmová spolupráce probíhala víceméně tak, jak bylo popsáno ve specifikaci. Projektový
tým se pravidelně scházel interně a příležitostně i se supervizorem projektu. Samozřejmostí
také byly diskuse s konzultantem, které zastřešoval jeden z členů týmu.

Původně bylo naplánováno, že se projekt rozdělí do tří separátních Django aplikací,
přičemž každý člen týmu bude garantovat jednu z nich. Tento plán se však ukázal jako
nevhodný, protože toto členění bylo příliš hrubé, a proto jsme přistoupili k jemnějšímu dělení
na konečných 12 aplikací. Každý člen týmu namísto garantování 1 aplikace garantoval zhruba
4 aplikace. Veškeré změny procházeli skrze code review jiného člena týmu (obvykle přiděleného
reviewera).

Verzování kódu probíhalo na platformě Github. Hlavní větev `master` byla chráněna proti
zápisům a veškeré změny probíhaly formou Pull Requests. Z vlastností Githubu jsme využívali
také Github Actions, které jsme použili pro automatickou kontrolu běhu migrací, automatický
deployment na testovací prostředí a také generování a deployment dokumentace na GitHub Pages.

Oproti naplánovanému harmonogramu se projekt výrazně zpozdil. Příčin bylo několik.
Jednou z nich bylo celkové podcenění náročnosti projektu a také fakt, že žádný z členů
týmu neměl předchozí zkušenosti s frameworkem Django. Dalším důvodem zdržení byly menší
časové kapacity jednotlivých členů týmu.

Abychom mitigovali zpoždění odevzdání, přistoupili jsme k důkladnějšímu plánování práce, což
vedlo k vytvoření milníků pro jednotlivé oblasti. Tento postup nám umožnil zpoždění zvládnout
a připravit projekt k odevzdání v řádném termínu.
