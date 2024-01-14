***************************************
Export účetních podkladů
***************************************

Systém umožňuje vyexportovat účetní podklady pro snadnější další zpracování. Vyexportovat
lze jednak odměny (většinou výplaty) a také příjmy (typicky platby za akce nebo zapůjčení
vybavení).

Export odměn
------------

Export odměn je možné provést z nabídky **Transakce** -> **Export podkladů**. Výsledkem je
soubor ve formátu CSV, který lze otevřít v jakémkoliv tabulkovém procesoru (např. MS Excel).
Jako oddělovač jednotlivých sloupců se používá středník, pro lepší kompatibilitu s nástrojem
MS Excel v české lokalizaci.

Ve vyexportovaném souboru je každá osoba s nějakou odměnou na více řádcích.
Na prvním řádku je uvedeno jméno osoby a celková částka, kterou má dostat. Na dalších řádcích
je potom odměna rozepsána po jednotlivých typech akcích (je tedy například možné, kolik si
daná osoba vydělala za trénování dětí). Tento rozklad se zobrazí jen v případě, že má osoba
zadanou hodinovou sazbu za daný typ akce.

Příklad vyexportovaného souboru:
::

  Novák;Jan;;;2000
  ;;plavecke;200;1000
  ;;lezecke;500;1000

V tomto příkladu má Jan Novák celkem dostat 2000 Kč. Z toho 1000 Kč za plavecké tréninky
a 1000 Kč za lezecké.

Export dluhů (příjmů)
---------------------

Na rozdíl od odměn, které nelze exportovat přímo ve formátu vhodném pro účetní software
(z důvodu vlastností tohoto softwaru), lze dluhy naimportovat přímo do účetního programu
POHODA jako vystavené faktury.

Export dluhů lze provést také v nabídce **Transakce** -> **Export podkladů**. Výsledkem je
xml soubor, který lze následně naimportovat přímo do účetního programu POHODA.

Import v programu pohoda se dá provést pomocí kontextové nabídky **Soubor** -> **Datová komunikace**
-> **XML import/export**. V otevřeném dialogovém okně je následně třeba vybrat vstupní soubor a dokončit
tento dialog. Následně se již v seznamu vydaných faktur objeví naimportované platby.