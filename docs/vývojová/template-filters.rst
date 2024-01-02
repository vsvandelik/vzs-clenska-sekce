***************************************
Template filters
***************************************
Šablonovací nástroj Jinja umožňuje provádět transformaci dat pomocí tzv. filtrů. Mnoho užitečných filtrů je v základní instalaci vestavěno. Typickým příkladem může být filtr ``length``, který odpovídá funkci ``len`` v Pythonu. 

V závislosti na doméně aplikace se můžou hodit další vlastní filtry, jejichž použití zjednoduší a zpřehlední kód. Tato funkcionalita je taktéž součástí nástroje Jinja a je hojně využívána všemi aplikacemi :term:`IS`.

:term:`IS` obsahuje filtry obecné a specifické. Obecné filtry považujeme za rozšíření běžných vestavěných filtrů nástroje Jinja. Tyto filtry jsou obvykle používány více nesouvisejícími aplikace, proto jsou součástí aplikace :ref:`vzs`, kde se nacházejí v adresáří templatetags/vzs_filters.py. Příkladem může být např. filtr ``negate``, který vrátí hodnotu s opačným znaménkem a filtr index, který vrátí i-tý prvek iterovatelné kolekce.