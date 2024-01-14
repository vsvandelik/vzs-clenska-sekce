# Členská sekce Vodní záchranné služby Praha 15

Informační systém pro neziskovou organizaci Vodní záchranná služba ČČK Praha 15, který 
umožňuje správu členů, akcí, tréninků pro děti a dalších souvisejících agend.

## Použité technologie

- Python s frameworkem Django
- Bootstrap
- AdminLTE

## Instalace

Prerekvizity:
- Python ≥ 3.11
- Node.js ≥ 17.0.0

1. Překopírujeme soubor ``.env.dist`` do ``.env`` a provedeme nastavení proměnných dle nápovědy u každé proměnné. Doporučujeme vycházet z následujícího nastavení proměnných, pokud jiné hodnoty nejsou k dispozici.

```
DEBUG=True 
SECRET_KEY=django-insecure
GOOGLE_DOMAIN= 
FIO_TOKEN= 
```

2. Nainstalujeme závislosti nutné ke spuštění, spustíme migrace a lokální webový server

```console
npm install
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8080
```

Pro kompletní postup instalace na lokálním i produkčním prostředí doporučujeme nahlédnout do [instalační dokumentace](https://vsvandelik.github.io/vzs-clenska-sekce/instala%C4%8Dn%C3%AD/installation.html).

## Přispívání

Kompletní postup pro přispívání do projektu je dostupný v [dokumentaci pro přispěvatele](https://vsvandelik.github.io/vzs-clenska-sekce/v%C3%BDvojov%C3%A1/contribute.html).

## Dokumentace

Dokumentace je dostupná na adrese [https://vsvandelik.github.io/vzs-clenska-sekce](https://vsvandelik.github.io/vzs-clenska-sekce).

## Autoři

Systém vznikl jako projekt na Matematicko-fyzikální fakultě Univerzity Karlovy v rámci 
předmětu Týmový projekt. 

Autoři projektu jsou:
- [Peter Fačko](https://github.com/papundekel)
- [Jakub Levý](https://github.com/jakublevy)
- [Vojtěch Švandelík](https://github.com/vsvandelik)

Projekt by nevznikl bez velké podpory a směřování supervizora projektu [RNDr. Martina Svobody, Ph.D.](https://www.ksi.mff.cuni.cz/~svoboda/) a bez 
podpory organizace [Vodní záchranná služba ČČK Praha 15](https://vodnizachranar.cz/), zastoupenou Lukášem Kordíkem, předsedou organizace.

## Licence

Tento projekt je licencován pod licencí MIT - pro více informací viz soubor [LICENSE](LICENSE.txt).

