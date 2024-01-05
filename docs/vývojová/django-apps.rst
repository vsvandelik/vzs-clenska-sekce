**************************
Popis Django aplikací
**************************

Tato stránka obsahuje všechny Django aplikace a jejich popis.

.. _api:

--------------------------------------
api
--------------------------------------
Tato aplikace obsahuje implementaci API. Více o API se je možné dozvědět na zvláštní stránce :doc:`./api`.

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
Model aplikace positions definuje vlastnosti pozic mezi které patří: název (``name``), hodinový příplatek za pozici (``wage_hour``), požadované kvalifikace/oprávnění/vybavení (``required_features``), věkové omezení (``min_age``, ``max_age``), skupina, v níž je vyžadováno členství (``group``)  a omezení na typ členství (``allowed_person_types``). Poskytuje také několik metod, které usnadní práci s modelem. Významnou metodou je ``does_person_satisfy_requirements``, která ověřuje, zda osoba splňuje požadavky na pozici k určitému datu.

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