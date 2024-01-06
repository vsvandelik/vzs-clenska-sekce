**************************
Popis Django aplikací
**************************

Tato stránka obsahuje všechny Django aplikace a jejich popis.

.. _api:

--------------------------------------
api
--------------------------------------
Tato aplikace obsahuje implementaci API. 

Model
^^^^^^^^^^^^^^^^^
Model aplikace :ref:`api` rozšiřuje funkčnost modelu Token, který je součástí :ref:`djangorestframework`. Rozšíření spočívá v přidání atributu :py:attr:`~api.models.Token.name` (jméno tokenu).

Mezi další důležité atributy, které jsou obsaženy v rodiči, patří:

- :py:attr:`~api.models.Token.created` (datum a čas vytvoření) 
- :py:attr:`~api.models.Token.key` (API klíč), pokud jeho hodnota není vyplněna, bude při uložení modelu automaticky vygenerována.

.. image:: ../_static/api-model.png
    :target: ../_static/api-model.png

Více informací API, včetně příkladů použítí, je možné se dozvědět na zvláštní stránce :doc:`./api`.

.. _events:

--------------------------------------
events
--------------------------------------

.. _features:

--------------------------------------
features
--------------------------------------

.. _groups:

--------------------------------------
groups
--------------------------------------
Aplikace groups definuje skupiny, ve kterých se sdružují osoby. Součástí aplikace je několik pohledů, šablon a formulářů pro správu skupin.

.. Každá skupina má definováno zda využívá synchronizaci s odpovídající skupinou v Google Workspace. Pokud je synchronizace povolena, tak je skupina uvnitř :term:`IS`  změna členství v  jedné libovolné straně se promítne do členství na straně druhé.

Model
^^^^^^^^^^^^^^^^^
Mezi atributy definované modelem patří:

- :py:attr:`~groups.models.Group.name` (jméno)
- :py:attr:`~groups.models.Group.google_email` (emailová adresa skupiny uvnitř Google Workspace)
- :py:attr:`~groups.models.Group.google_as_members_authority` (flag indikující, zda Google skupina s emailovou adresou :py:attr:`~groups.models.Group.google_email` je autoritou)
- :py:attr:`~groups.models.Group.members` (seznam členů skupiny)

.. image:: ../_static/groups-model.png
    :target: ../_static/groups-model.png

.. _one_time_events:

--------------------------------------
one_time_events
--------------------------------------


.. _pages:

--------------------------------------
pages
--------------------------------------
Aplikace pages definuje statické stránky, které je možné prohlížet a editovat.


Model
^^^^^^^^^^^^^^^^^
Model je určen k ukládání statických stránek. Každá stránka obsahuje:

- :py:attr:`~pages.models.Page.title` (název)
- :py:attr:`~pages.models.Page.content` (obsah ve formátu HTML)
- :py:attr:`~pages.models.Page.slug` (URL slug) 
- :py:attr:`~pages.models.Page.last_update` (datum a čas poslední aktualizace)


.. image:: ../_static/pages-model.png
    :target: ../_static/pages-model.png

.. _persons:

--------------------------------------
persons
--------------------------------------

.. _positions:

--------------------------------------
positions
--------------------------------------
Aplikace positions definuje pozice, které jsou přiřazeny k jednorázovým událostem i tréninkům pomocí :py:class:`~events.models.EventPositionAssignment`, které navíc specifikuje další atributy jako např. počet lidí, kteří jsou na pozici vyžadováni. Součástí aplikace je několik pohledů, šablon a formulářů pro správu pozic.

Model
^^^^^^^^^^^^^^^^^
Model aplikace :ref:`positions` definuje atributy pozic mezi které patří: 

- :py:attr:`~positions.models.EventPosition.name` (název)
- :py:attr:`~positions.models.EventPosition.wage_hour` (hodinový příplatek za pozici)
- :py:attr:`~positions.models.EventPosition.required_features` (požadované kvalifikace/oprávnění/vybavení)
- :py:attr:`~positions.models.EventPosition.min_age`, :py:attr:`~positions.models.EventPosition.max_age` (věkové omezení)
- :py:attr:`~positions.models.EventPosition.group` (skupina, v níž je vyžadováno členství)
- :py:attr:`~positions.models.EventPosition.allowed_person_types` (omezení na typ členství)

Model také poskytuje také několik metod, které usnadní práci s modelem. Významnou metodou je :py:meth:`~positions.models.EventPosition.does_person_satisfy_requirements`, která ověřuje, zda osoba splňuje požadavky na pozici k určitému datu.

.. image:: ../_static/position-model.png
    :target: ../_static/position-model.png

.. _trainings:

--------------------------------------
trainings
--------------------------------------

.. _transactions:

--------------------------------------
transactions
--------------------------------------

.. _users:

--------------------------------------
users
--------------------------------------

.. _vzs:

--------------------------------------
vzs
--------------------------------------
Aplikace :ref:`vzs` má speciální postavení, jedná se o první a tudíž výchozí aplikaci celého projektu. Její součástí není konkrétní specifická funkcionalita, tato aplikace pouze sdržuje nezařaditelný společný kód, různé pomocné funkce a nachází se zde konfigurace celého projektu.

Aplikace nevyužívá konkrétní model, v souboru ``models.py`` se nachází pouze několik obecných ``Mixin`` tříd, např. :py:class:`~vzs.models.ExportableCSVMixin`, které je možné použít na libovolný model a zajistit tak funkci exportu do formátu CSV.