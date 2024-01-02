**************************
Použitá Django rozšíření
**************************
Tato stránka obsahuje seznam všech použitých Django rozšíření včetně krátkého popisu a způsobu využití.

- :ref:`django-active-links`
- :ref:`django-crispy-forms`
- :ref:`django-crontab`
- :ref:`django-environ`
- :ref:`django-polymorphic`
- :ref:`django-macros`
- :ref:`django-mptt`
- :ref:`django-select2`
- :ref:`django-tempus-dominus`
- :ref:`django-tinymce`
- :ref:`djangorestframework`

.. _django-active-links:

------------------------
django-active-links
------------------------
django-active-links nabízí jednoduchý způsob, kterým je možné zvýrazit aktivní záložku v menu. Zvýraznění aktivních položek na levém bočním panelu závisí na tomto balíku.

.. _django-crontab:

------------------------
django-crontab
------------------------
Toto rozšíření umožňuje vybrat funkce a nastavit jim periodu, se kterou budou volány pomocí Cronu. :term:`IS` tuto funkcionalitu využívá např. k periodické kontrole uzavírání událostí. 

Bližší informace o použití Cronu viz :ref:`funkce_volane_daemonem_cron`.

.. _django-crispy-forms:

----------------------
django-crispy-forms
----------------------
Umožnuje flexibilnější nastavení renderování Django forem. :term:`IS` konkrétně používá nastavení ``CRISPY_TEMPLATE_PACK = "bootstrap4"``, které aplikuje Bootstrap 4 na všechny formulářové prvky. Více informací o formulářích se nachází na zvláštní stránce :doc:`./forms`.

.. _django-environ:

----------------------
django-environ
----------------------
django-environ je rozšíření, která umožňuje načítání environmentálních proměnných. :term:`IS` obsahuje několik konfiguračních proměnných v souboru :ref:`.env`, které jsou načítány při spuštění.

.. _django-polymorphic:

----------------------
django-polymorphic
----------------------
django-polymorphic implementuje polymorfismus u modelů. Modely se poté chovají obdobně jako třídy v objektově orientovaném programování. Více informací o polymorfních modelech se nachází na stránce :ref:`polymorfni_modely`.

.. _django-macros:

----------------------
django-macros
----------------------
django-macros je užitečné, pokud máme části Jinja šablony, kterou chceme opakovat. django-macros umožňuje vytvářet makra a opakovatelné bloky. :term:`IS` konkrétně využívá pouze ``repeated_block`` a ``repeat`` pro nadpis stránky, který se zadefinuje do bloku a poté opakuje ještě do tagu ``<title>``.

.. _django-mptt:

-----------------
django-mptt
-----------------
Kvalifikace, oprávnění a vybavení jsou stromová data, která se mohou nekonečně větvit, pro jednodušší práci a renderování těchto dat slouží balíček django-mptt.

.. _django-select2:

-----------------
django-select2
-----------------
Tento balíček umožňuje použít Select2 idiomatickým způsobem z pohledu Djanga. Více informací o Select2 viz :ref:`Select2`.

.. _django-tempus-dominus:

----------------------
django-tempus-dominus
----------------------
Výchozí HTML komponenta pro výběr data a času nezobrazuje formát obvyklý pro Česko. django-tempus-dominus umožňuje integraci nástroje pro výběr data a času Tempus Dominus Bootstrap 4, který je lépe konfigurovatelný a zobrazuje čas v obvyklém formátu.

.. _django-tinymce:

---------------
django-tinymce
---------------
django-tinymce poskytuje komponenty pro integraci WYSIWYG editoru, který :term:`IS` využívá v aplikaci :ref:`pages` pro tvorbu statických stránek.


.. _djangorestframework:

------------------------
djangorestframework
------------------------
Balíček sloužící k tvorbě API. Využíván aplikací :ref:`api`.