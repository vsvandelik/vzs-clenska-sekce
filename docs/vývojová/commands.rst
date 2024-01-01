.. _vlastni_django_prikazy:

***************************************
Vlastní Django příkazy
***************************************
Tato stránka obsahuje seznam všech vytvořenych vlastních Django příkazů včetně jejich popisu.

.. list-table::
   :widths: 10 40 40
   :header-rows: 1

   * - Název příkazu
     - Cesta
     - Popis
   * - check_unclosed_one_time_events
     - one_time_events/management/commands/check_unclosed_one_time_events.py
     - Odešle upozornění na neuzavřené události správcům kategorií událostí a organizátorům. Tento příkaz je periodicky volán Cronem.
   * - check_unclosed_trainings
     - trainings/management/commands/check_unclosed_trainings.py
     - Odešle upozornění na neuzavřené tréninky správcům kategorií tréninků a organizátorům. Tento příkaz je periodicky volán Cronem.
   * - convert_old_system_data
     - vzs/management/commands/convert_old_system_data.py
     - Převede CSV soubor s uživateli ze starého systému na data ve formátu JSON, který je možné načíst do :term:`IS` Více o konverzi viz :doc:`../uživatelská/data-conversion`.
   * - createsuperuser
     - overriden_django_commands/management/commands/createsuperuser.py
     - Vytvoří nového administrátorského uživatele se všemi povoleními.
   * - fetch_fio
     - transactions/management/commands/fetch_fio.py
     - Synchronizuje transakce provedené na bankovním účtu :term:`Organizace`.
   * - garbage_collect_tokens
     - users/management/commands/garbage_collect_tokens.py
     - Smaže expirované tokeny pro obnovu hesel z databáze. Tento příkaz je periodicky volán Cronem.
   * - generate_one_time_events
     - one_time_events/management/commands/generate_one_time_events.py
     - Vytvoří nové jednorázové události.
   * - generate_persons
     - persons/management/commands/generate_persons.py
     - Vytvoří nové osoby.
   * - generate_positions
     - positions/management/commands/generate_positions.py
     - Vytvoří nové pozice.
   * - generate_trainings
     - trainings/management/commands/generate_trainings.py
     - Vytvoří nové tréninky.
   * - generate_transactions
     - transactions/management/commands/generate_transactions.py
     - Vytvoří nové transakce.
   * - send_feature_expiry_mail
     - features/management/commands/send_feature_expiry_mail.py
     - Odešle email osobám, kterým brzy vyprší vlastnost. Tento příkaz je periodicky volán Cronem.
   * - sync_groups
     - groups/management/commands/sync_groups.py
     - Synchronizuje skupiny v :term:`IS` se skupinami v Google Workspace.


-----------------------------------
Spouštění příkazů
-----------------------------------
Příkaz názvem ``cmd1`` můžeme spustit spuštěním ``python ./manage.py cmd1``. Platí, že název příkazu odpovídá názvu souboru bez přípony. 

Příklad:

.. code-block:: console

    python ./manage.py createsuperuser

Některé příkazy přijímají další parametry. Pro zobrazení nápovědy je možné použít přepínač ``-h``.