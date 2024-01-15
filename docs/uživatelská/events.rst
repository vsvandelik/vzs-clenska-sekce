***************************************
Akce a tréninky
***************************************

Jednoznačně nejdůležitější a nejkomplexnější částí systému je správa akcí.

Akce jsou dvojího typu:

- Tréninky
- Jednorázové akce

Každá akce se skládá z několika částí:

- základní informace o akci (datum konání, místo konání, popis, ...)
- seznam účastníků (rozdělených do skupin schválení, náhradníci, odmítnutí)
- seznam organizátorských pozic (řidič, vedoucí, ...)
- seznam organizátorů (jaký den je kdo organizátorem na jaké pozici)

Základní rozdíl mezi účastníky a organizátory je především v tom, že účastníci za svou
účast typicky platí (lze ale nastavit i nulový poplatek) a přihlašují se vždy na celou dobu.

Organizátoři se naopak přihlašují vždy na konkrétní pozice, mohou se přihlásit jen
na část akce (v případě vícedenní akce) a za svou účast naopak typicky dostávají plat (ale
ten opět může být nulový).

Přidávání akcí
--------------

Akce se dají přidávat prostřednictvím tlačítka **Přidat akci**, příp. **Přidat trénink** (pokud
má osoba patřičná oprávnění). V obou případech se zobrazí formulář pro zadání základních
informacích o akci.

Jedno z dostupných polí je **Přidat nové účastníky jako***. Toto pole určuje, jestli
se účastníci mohou přihlašovat na akci přímo, anebo je třeba, aby správce akce každého jednoho
účastníka schválil.

U jednorázových akcí se navíc nastavuje počet hodin akce každý den. Tento údaj se používá
pro výpočet odměn na základně hodinových sazeb jednotlivých organizátorů. Dále mají jednorázové
akce navíc pole **Standardní výše poplatku pro účastníky**, které určuje, kolik budou účastníci
za akci platit. Poplatek je ale možné dále individuálně změnit.

U tréninků neexistuje žádné speciální pole. Jediné omezení je, že tréninky musejí probíhat alespoň
po dobu 14 dní.

Organizátorské pozice
---------------------

Každá akce má svůj seznam organizátorských pozic. Tyto pozice se dají přidávat prostřednictvím
detailu akce ze seznamu, který se definuje v záložce **Správa událostí** -> **Pozice**.

U každé pozice je definováno, jaké požadavky musí osoba splňovat, aby se mohla na pozici
přihlásit. Rovněž je zde uveden hodinový příplatek za vykonávání pozice. Tento příplatek umožňuje
odměnit organizátory nad rámec jejich standardních hodinových sazeb.

Každá akce může mít neomezené množství pozic a je možné zadat, že na akci je kapacita
pro více lidí na stejné pozici.

Stavy akcí a docházka
---------------------

S akcemi je spojen i schvalovací workflow. Každá akce může mít jeden ze tří stavů:

- **neuzavřena** - akce prozatím neproběhla, či nebyla vyplněna docházka účastníků a organizátorů
- **uzavřena** - akce již proběhla a docházka byla vyplněna
- **zpracována** - správce zkontroloval docházku a zadal organizátorům odměny do systému

U tréninků se tyto stavy týkají jednotlivých výskytů tréninku.

Docházku u tréninku vyplňuje garant tréninku (hlavní trenér). Schvalování následně provádí
správce tréninků.

U jednorázových akcí docházku i schvalování provádí správce akcí.

Specifika tréninků
--------------------

Tréninky jsou specifické tím, že se opakují po delší období a klidně i s několika výskyty týdne.
Účastníci si mohou vybrat, na které výskyty se přihlásí (například jestli budou chodit každé
pondělí a pátek či jenom pondělky). Organizátoři jsou určení vždy na celý trénink.

V případě, že se účastník omluví z tréninku včas a trenér potvrdí, že na omluvený trénink
skutečně nepřišel, je tomuto účastníkovi umožněno se přihlásit na náhradní trénink. Náhradním
tréninkem může být buď jiný výskyt stejného tréninku, nebo jiný trénink (seznam tréninků
k nahrazení může správce tréninků definovat v detailu tréninku).

Potřebná povolení
-----------------

Pro každý typ tréninku i jednorázové akce existuje speciální povolení, které může správce
systému osobě přidělit.

V případě tréninků se jedná o:

- Správce plaveckých tréninků
- Správce lezeckých tréninků
- Správce zdravovědy

V případě jednorázových akcí se jedná o:

- Správce komerčních událostí
- Správce kurzů
- Správce prezentačních událostí
- Správce událostí pro děti
- Správce společenských událostí

Pozice na akcích může spravovat kdokoliv, kdo má alespoň jedno z výše uvedených povolení.

Transakce spojené s akcemi
--------------------------

Každá akce může mít několik transakcí spojených s účastníky a organizátory. V případě účastníků
na jednorázových akcích se transakce generuje v okamžiku schválení účastníka (přihlášení jako
schválený účastník). Dokud účastník částku neuhradil, je možné ji upravovat.

U tréninků se transakce generují manuálně pro všechny přihlášené účastníky pomocí tlačítka
**Přidat transakci** v detailu tréninku.

V případě organizátorů se transakce (odměny) generují automaticky v okamžiku, kdy se akce
přepne do stavu **zpracována**.