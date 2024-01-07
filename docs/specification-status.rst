##########################
Vypořádání specifikace
##########################

Na této stránce popisujeme rozdíly ve finální implementaci oproti specifikaci,
která byla schválena projektovou komisí. U jednotlivých odlišností uvádíme i důvod,
proč k dané změně došlo.

Pro referenci je možné si přečíst specifikaci v souboru :download:`specifikace.pdf <_static/specifikace.pdf>`.

Změna osobních údajů samotnou osobou a následné schválení správcem
------------------------------------------------------------------
(str 6; "Změna údajů může probíhat i tak, že uživatel navrhne změnu a jiný uživatel s dostatečným oprávněním mu změnu schválí a provede.")

K DISKUSI.

Evidence služby na Orlíku
-------------------------
(str. 6; ". Z těchto důvodu je potřeba evidovat služby během letních měsíců ...)

K DISKUSI. Lze implementovat pomocí jednorázových akcí, případě vyargumentovat jinak.

Závazky za tréninky
-------------------
(str. 13; "Platební povinnost za celý školní rok je rozdělena na 3 části.")

Zvolili jsme obecnější řešení, které umožňuje dynamický počet plateb za tréninky v průběhu roku.

Statický typy jednorázových událostí
------------------------------------
(str. 14; "Typy se budou evidovat dynamicky v IS.")

V našem řešení se nakonec typy jednorázových událostí řeší staticky, protože z větší analýzy potřeb organizace vyplynulo, že se typy událostí nebudou měnit.

Zákaz přihlášení jen na část události jako organizátor
------------------------------------------------------
(str. 14; "Osoby se mohou na Událost (Pozici) přihlásit jen na část doby (definováno pomocí půldnů), pokud to nastavení Události dovolí.")

K DISKUSI.

Nezapočítávání kvalifikací do výpočtu odměn
-------------------------------------------
(str. 14; "Do výpočtu odměny se rovněž zohledňují parametry z profilu Osoby (např. nejvyšší dosažená kvalifikace).")

Nakonec jsme zvolili řešení přes evidenci hodinových sazeb u jednotlivých osob, které umožňuje reflektovat skutečný stav věci v závislosti na aktuálně uzavřeném pracovněprávním vztahu.

Změny v entitách a vztazích
---------------------------
(str. 15 až 18)

V reálné implementaci došlo k několika dílčím změnám v návrhu oproti kapitole 3.2 Entity a vztahy. Tyto úpravy vycházely především z potřeb organizace a dalších návazností systému, které se ukázaly až v průběhu implementace. Změny jsou malého rozsahu (např. evidence údaje navíc u osoby oproti předepsanému seznamu). Větší změna nastala u struktury událostí, kdy jsme opustili původní stromový návrh událostí a využili raději plochý návrh, který umožnil přímočařejší implementaci.

Účty vs. osoby
--------------
(str. 18; "Má možnost novou Osobu přidat ke stávajícímu Účtu, nebo jí založit nový.")

Nakonec jsme zvolili řešení, které ale vede ke stejnému cíli. Každá osoba má účet, ale jedna osoba může spravovat i jiné osoby.

Odebírání osoby
---------------
(str. 18; " Historie Osoby zůstane zachovaná, ale odeberou se osobní a kontaktní údaje o Osobě.")

Zvolili jsme sofistikovanější řešení – pokud osoba v systému nemá žádné trvalé stopy (účast na akcích především), tak je smazána úplně. V opačném případě je anonymizována, dle původní specifikace.

Přihlášení na trénink ve veřejné části systému
----------------------------------------------
(str. 19; "Dítě, které prozatím není v systému, si ve veřejné části IS vyplní přihlášku, kde si vybere, kam chce docházet, a zároveň si i vytvoří uživatelský Účet. ")

Toto chování nebylo po dohodě s organizací implementováno, protože to odporuje reálnému procesu v organizaci, kdy administrátoři zakládají osoby ručně, až po návštěve dítěte na prvním ukázkovém tréninku.

Rozdělení na Django aplikace
----
(str. 28; "...je možné IS rozdělit na tři aplikace: Users, Members a Events.")

Nakonec jsme :term:IS rozdělili na více aplikací, aby byla možná lepší distribuce práce a přehlednost kódu. Výsledným počtem je 11 aplikací.

Datový model
----
(str. 28)

Datový model doznal větších úprav z důvodu efektivity výsledného kódu, ale základní myšlenky zůstaly zachované.

Use-cases
----
(str. 30)

Podobně jako u datového modelu i zde došlo k větším úpravám. Myšlenka všech scénářů zůstala zachována, ale podoba a umístění tlačítek a celkový proces byl upraven, aby lépe odpovídal výslednému systému.

Harmonogram
----
(str. 40)

K velkému zdržení došlo u harmonogramu. Zdržení bylo způsobeno především časovým vytížením některých členů projektového týmu v průběhu letních prázdnin a podzimu.