***************************************
Autorizace
***************************************

:term:`IS` pro autorizaci využívá vestavěné prostředky od Djanga,
ale podstatně je upravuje.

-----
Model
-----
Používáme vestavěný model, tedy každé povolení má instanci
a každý uživatel má přiřazena nějaká povolení.

Standardně lze definovat povolení ve třídě ``Meta`` každého modelu.
V našem případě jsme zvolili definovat pro jednoduchost povolení pouze
v modelu ``users.models.Permission``.

------------------------
Aktivní osoba a uživatel
------------------------
Autorizace se týká koncept aktivní osoby. Přihlášený uživatel má možnost
přepínat si aktivní osobu, přičemž aktivní osobou může být přiřazena osoba uživatele
nebo osoba, která je danou osobou spravována.
Aktivní osoby jsou implementovány pomocí sessions.

Je-li uživatel přihlášen a aktivní osoba má přiřazeného uživatele,
aktivním uživatelem je dán přiřazený uživatel.
Jinak je aktivním uživatelem ``AnonymousUser``, který nemá žádná povolení.

--------------------
Vyžadování povolení
--------------------
Všechna povolení v :term:`IS` jsou vyžadována relativně k aktivnímu uživateli.
Tak je umožněno uživateli přepnutím aktivní osoby interagovat se systémem
"očima" jiné osoby.

Pro vyžadování povolení ve views je nutné dědit třídu
``users.permissions.PermissionRequiredMixin``.
Tato třída rozšiřuje třídu ``django.contrib.auth.mixins.PermissionRequiredMixin`` tak,
aby bylo možné vyžadovat různá povolení pro různé HTTP metody,
a také, aby se dal testovat přístup k view bez zaslání HTTP requestu.

Pro snadné vyžadování povolení slouží class variables ``permissions_formula``,
``permissions_formula_GET`` a ``permissions_formula_POST``.
Všechny jsou ve tvaru DNF formulí s názvy povolení jako proměnnými.
``_GET`` a ``_POST`` verze mají přednost, pokud jsou definovány,
a zužují význam na konkrétní HTTP metodu.

Při složitější logice může být nutné přepsat metodu ``view_has_permission``
s tímto předpisem::

    @classmethod
    def view_has_permission(cls, metoda: str, active_user, GET, POST, **kwargs):

``kwargs`` obsahuje path parametry, ``GET`` query parametry jako slovník
a ``POST`` parametry z těla requestu jako slovník.

Možnost testovat povolení bez zaslání HTTP requestu je využita
při podmíněném zobrazování v šablonách. Typicky jde o zobrazení tlačítka pouze v případě,
že má uživatel povolení k jeho stlačení.
Existují dva template tagy, které toto umožňují: ``perm_url`` a ``ifperm``.
Použití je následující::

    {% load vzs_filters %}

    {% perm_url "app:pattern" object.pk as perm_outer %}
    ...

    {% if perm_outer %}
        <a href="{{ perm_outer.url }}">...</a>
    {% endif %}
    ...
    {% if perm_outer %}
        ...
    {% endif %}

    {% ifperm "app:pattern" object.pk as perm %}
        <a href="{{ perm.url }}">...</a>
    {% endifperm %}

Rozdíl je tedy takový, že ``perm_url`` je obecnější a dovoluje oddělit vyhodnocení
a podmíněný blok. ``ifperm`` je forma pro speciální případ, který je ale nejčastější.

Template tagy pro testování podmínek posílají do ``view_has_permission``
hodnoty pro ``GET`` i ``POST`` jako prázdný slovník.
