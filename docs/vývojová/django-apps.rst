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
Model aplikace :ref:`api` rozšiřuje funkčnost modelu Token, který je součástí :ref:`djangorestframework`. Rozšíření spočívá v přidání atributu ``name`` (jméno tokenu).

Mezi další důležité atributy, které jsou obsaženy v rodiči, patří:

- ``created`` (datum a čas vytvoření) 
- ``key`` (API klíč), pokud jeho hodnota není vyplněna, bude při uložení modelu automaticky vygenerována.

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

.. _one_time_events:

--------------------------------------
one_time_events
--------------------------------------


.. _pages:

--------------------------------------
pages
--------------------------------------

.. _persons:

--------------------------------------
persons
--------------------------------------

.. _positions:

--------------------------------------
positions
--------------------------------------
Aplikace positions definuje pozice, které jsou přiřazeny k jednorázovým událostem i tréninkům pomocí ``EventPositionAssignment``, které navíc specifikuje další vlastnosti jako např. počet lidí, kteří jsou na pozici vyžadováni.

Model
^^^^^^^^^^^^^^^^^
Model aplikace :ref:`positions` definuje vlastnosti pozic mezi které patří: název (``name``), hodinový příplatek za pozici (``wage_hour``), požadované kvalifikace/oprávnění/vybavení (``required_features``), věkové omezení (``min_age``, ``max_age``), skupina, v níž je vyžadováno členství (``group``)  a omezení na typ členství (``allowed_person_types``). Poskytuje také několik metod, které usnadní práci s modelem. Významnou metodou je ``does_person_satisfy_requirements``, která ověřuje, zda osoba splňuje požadavky na pozici k určitému datu.

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