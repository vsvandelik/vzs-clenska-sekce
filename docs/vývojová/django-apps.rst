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
Události jsou vždy jedním ze dvou druhů; buďto se jedná o jednorázové události, nebo tréninky. Většina operací prováděná nad událostmi bez ohledu jejich na druh má společný základ, který je implementován právě v aplikace :ref:`events`. Specifická funkcionalita závislá na druhu události je potom zajištěna pomocí dědičnosti a nachází se v aplikacích :ref:`one_time_events`, nebo :ref:`trainings`.

Součástí aplikace jsou template filtery specifické pro doménu událostí, které se nachází v souboru templatetags/events_template_tags.py. Více o template filtrech je možné se dočíst v části :doc:`./template-filters`.

Formuláře patřící do této aplikace zpravidla implementují pouze společný základ pro jednorázové události a tréninky, konečná implementace využívaného formuláře se nachází v aplikacích :ref:`one_time_events` a :ref:`trainings`.

Mezi pohledy implementované v této aplikaci v souboru views.py patří hlavně pohledy končící textem ``DeleteView``, které dle konvencní Djanga značí pohled, který maže objekt z databáze. Tuto funkcionalitu je možné implementovat na úrovni této aplikace, protože ``generic.DeleteView``, z kterého dědí ``DeleteView`` pohledy této aplikace, používá ke smazání metodu ``delete`` na modelu, která je plně polymorfní díky použití rozšíření :ref:`django-polymorphic`.

Model
^^^^^^^^^^^^^^^^^
Aplikace :ref:`events` obsahuje několik modelů z nichž všechny kromě :py:class:`~events.models.EventPositionAssignment` jsou polymorfní a jsou dále rozšířeny v modelech aplikací :ref:`one_time_events` a :ref:`trainings`.

:py:class:`~events.models.EventPositionAssignment` definuje přiřazení pozice definované v aplikace :ref:`positions` k události. Model :py:class:`~events.models.EventPositionAssignment` navíc obsahuje atribut :py:attr:`~events.models.EventPositionAssignment.count` (počet osob, které jsou na danou pozici vyžadováni).

:py:class:`~events.models.ParticipantEnrollment` definuje přihlášku účastníka, obsahuje:

- :py:attr:`~events.models.ParticipantEnrollment.created_datetime` (datum a čas provedení přihlášky)
- :py:attr:`~events.models.ParticipantEnrollment.state` (stav přihlášky – schválen, náhradník, odmítnut)

:py:class:`~events.models.Event` definuje událost, obsahuje:

- :py:attr:`~events.models.Event.name` (název)
- :py:attr:`~events.models.Event.description` (popisek)
- :py:attr:`~events.models.Event.location` (místo konání)
- :py:attr:`~events.models.Event.date_start` (datum začátku)
- :py:attr:`~events.models.Event.date_end` (datum konce)
- :py:attr:`~events.models.Event.positions` (přiřazené pozice)
- :py:attr:`~events.models.Event.participants_enroll_state` (výchozí stav aplikované na nové účastníky)
- :py:attr:`~events.models.Event.capacity` (maximální počet účastníků)
- :py:attr:`~events.models.Event.min_age` (minimální věk účastníků)
- :py:attr:`~events.models.Event.max_age` (maximální věk účastníků)
- :py:attr:`~events.models.Event.group` (skupina, v níž je u účastníků vyžadované členství)
- :py:attr:`~events.models.Event.allowed_person_types` (typ členství vyžadovaný u účastníků)

:py:class:`~events.models.EventOccurrence` definuje jedno konání události, obsahuje:

- :py:attr:`~events.models.EventOccurrence.event` (událost)
- :py:attr:`~events.models.EventOccurrence.state` (stav události – neuzavřena, uzavřena, zpracována)

:py:class:`~events.models.OrganizerAssignment` definuje přiřazení organizátora ke dni konání události, obsahuje pouze:

- :py:attr:`~events.models.OrganizerAssignment.transaction` (transakce k proplacení za organizaci)

.. image:: ../_static/events-model.png
    :target: ../_static/events-model.png

.. _features:

--------------------------------------
features
--------------------------------------

.. _groups:

--------------------------------------
groups
--------------------------------------
Aplikace groups definuje skupiny, ve kterých se sdružují osoby. Součástí aplikace je několik pohledů, šablon a formulářů pro správu skupin.

Každá skupina má definováno zda využívá synchronizaci s odpovídající skupinou v Google Workspace (tj. zda je emailová adresa této skupiny vyplněna v atributu :py:attr:`~groups.models.Group.google_email`). Pokud je synchronizace povolena, tak změna členství na jedné straně se promítne do skupiny na druhé straně, případné konflikty se vyřeší dle nastavení atributu :py:attr:`~groups.models.Group.google_as_members_authority`.

Členství ve skupině může být použito jako jedno z kritérii určující oprávnění k přihlášení na pozici jako organizátor nebo jako účastník události.

Model
^^^^^^^^^^^^^^^^^
Mezi atributy definované modelem patří:

- :py:attr:`~groups.models.Group.name` (jméno)
- :py:attr:`~groups.models.Group.google_email` (emailová adresa skupiny uvnitř Google Workspace)
- :py:attr:`~groups.models.Group.google_as_members_authority` (flag indikující, zda Google skupina s emailovou adresou :py:attr:`~groups.models.Group.google_email` je autoritou při synchronizaci osob)
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