***************************************
Jak na
***************************************
Tato stránka obsahuje návody a ukázky kódu demonstrující použití běžných primitiv, které se často opakovaně vyskytují napříč všemi aplikacemi.


.. _Bootstrap_modals_example:

-------------------------
Modální okna Bootstrapu
-------------------------
Budeme vytvářet tlačítko a modální okno. Po stisku tlačítka se zobrazí modální okno.

Vytvoření tlačítka
^^^^^^^^^^^^^^^^^^^^^^^^
Rozmyslíme si id modálního okna, které budeme vytvářet v dalším kroku. Definujeme ho jako ``"unenroll-myself-participant-modal"``. Modální okno bude zobrazovat odpověď požadavku z akce ``{% url 'events:unenroll-myself-participant' active_person_enrollment.id %}``, která je dobře definována.

Potom můžeme vytvořit tlačítko.

.. code-block:: console

    <a data-toggle="modal" data-target="#unenroll-myself-participant-modal" data-action="{% url 'events:unenroll-myself-participant' active_person_enrollment.id %}" class="btn btn-secondary">Odhlásit se jako účastník</a>

Důležité je nastavit správně atributy ``data-toggle``, ``data-target`` a ``data-action``, které souvisí s modálním oknem a požadavkem, který má nastat při zobrazení modálního okna.

Nyní je potřeba vytvořit modální okno.

Vytvoření modální okna Bootstrapu
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Pro vytvoření modálního okna existuje předpřipravená šablona, kterou stačí pouze vložit do naší stránky. Důležité je správně vyplnit parametr ``id``, je nutné, aby hodnota byla stejná jako atribut ``data-target`` u tlačítka, aby fungovalo zobrazení modálního okna po stisku tlačítka.

Příklad

.. code-block:: console

    {% include 'modal_include.html' with id='unenroll-myself-participant-modal' %}


Napojení JS na zobrazení modálního okna
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Nyní zbývá poslední krok a tím je spuštění JS. Při zobrazení modálního okna se musí odeslat request na URL endpoint definovaný v atributu ``data-action`` a vložit odpověď do modálního okna. To je možné provést jednoduše předpřipravenou funkcí ``registerModal(id)``.

Příklad:

.. code-block:: javascript

    registerModal("unenroll-myself-participant-modal")


.. _DataTable_example:

-------------------------
DataTables
-------------------------
Na existující tabulku s ``id="tokens-table"`` je možné DataTables aplikovat použitím funkce ``datatableEnable(id, searchableColumns, orderableColumns, order = [])``, nebo ``simpleOrderableTableEnable(id, orderableColumns, order = [])``. Druhá funkce skryje vyhledávací pole. Parametry ``searchableColumns`` a ``orderableColumns`` očekávají pole indexů sloupců. První parametr definuje sloupce, přes které se vyhledává při použití vyhledávacího pole. Druhý parametr definuje sloupce, které je možné řadit. Konečně parametr ``order`` definuje pořadí sloupců, tento parametr může být vynechán, pokud není potřeba měnit pořadí sloupců.

Příklad použití:

.. code-block:: console

    {% block scripts %}
        <script src="{% static "datatables.js" %}"></script>
        <script>datatableEnable("tokens-table", [0, 1], [0, 1, 2]);</script>
    {% endblock %}

.. _Select2_example:

-------------------------------
 Select2
-------------------------------
Pokud vytvoříme formulářové pole, které bude mít na výběr více položek. Django použije jako widget k renderování buďto radio button nebo select box v závislosti na počtu položek. Pokud chceme definovat použití Select2, musíme explicitně nastavit widget.

Příklad: Máme formulář s jedním políčkem ``"group"``, u kterého vynutíme použití Select2.

.. code-block:: python

    class GroupMembershipForm(ModelForm):
    class Meta:
        fields = ["group"]
        widgets = {
            "group": Select2Widget(),
        }

.. _vytvoreni_vlastniho_django_prikazu:

------------------------------------
 Vytvoření vlastního Django příkazu
------------------------------------
Vlastní Django příkaz se vždy nachází uvnitř nějaké aplikace. Je vhodné dodržovat konvenci, že příkazy se nachází uvnitř té aplikace, se kterou nejvíce souvisí jejich implementace. Relativně z pohledu aplikace se příkazy vždy nachází uvnitř adresáře ``management/commands/``. Vytvořením souboru ``management/commands/cmd1.py``, můžeme příkaz ``cmd1`` spustit spuštěním ``python ./manage.py cmd1``. Platí, že název příkazu odpovídá názvu souboru bez přípony. 

Soubory implementující příkazy musí vycházet z následující šablony. Při spuštění příkazu se spustí funkce handle.

.. code-block:: python

    class Command(BaseCommand):
        help = "TODO: Write here useful help message"

        def handle(self, *args, **options):
            # TODO: implement this function
            pass

.. _vytvoreni_vlastniho_filtru:

-------------------------------
Vytvoření vlastního filtru
-------------------------------
Nejprve je nutné se rozhodnout, zda filtr, který chceme vytvořit je obecný nebo specifický. Více informací o typech filtrů se nachází v dokumentu :doc:`./template-filters`.

Obecné filtry patří do souboru templatetags/vzs_filters.py aplikace :ref:`vzs`. Specifické filtry patří do konkrétní aplikace, která je bude využívat. Jako adresář doporučujeme opět použít templatetags/ a jako název souboru s filtry např. filters.py. 

Poté je potřeba se rozhodnout, zda chceme vytvořit template filter, template tag, inclusion tag, nebo simple tag. Mezi těmito primitivy jsou drobné rozdíly, většinou se hodí template filter, doporučujeme si přečíst `stránku na stackoverflow <https://stackoverflow.com/questions/5586774/django-template-filters-tags-simple-tags-and-inclusion-tags>`_, kde jsou rozdíly detailně popsány.

Po implementaci, která může např vypadat takto

.. code-block:: python

    @register.filter
    def addstr(arg1, arg2):
        return str(arg1) + str(arg2)

můžeme tento filtr používat v Jinja šablonách. Nesmíme však zapomenout na načtení souboru obsahující implementaci filtrů, např. ``{% load vzs_filters %}`` (bez přípony .py).

Příklad použití:

.. code-block:: console

    {% load vzs_filters %}
    <ul>
        <li>Jméno: {{ person.first_name|addstr:' '|addstr:person.last_name }}</li>
        ...
    </ul>

.. _funkce_volane_daemonem_cron:

-------------------------------
 Funkce volané daemonem Cron
-------------------------------
Libovolná funkce může být periodicky volána Cronem. Nicméně všechny funkce, které jsou volány Cronem jsou jednořádkové funkce spouštějící Django příkaz. Je doporučeno se této konvence držet při přidávání dalších funkcí pro Cron. Výhoda tohoto přístupu spočívá v tom, že je možné kdykoliv ručně příkaz spustit pomocí standardních nástrojů Djanga (``python ./manage.py <název příkazu>``).

Příkazy implementující funkcionalitu by se měly nacházet v aplikaci, která úsce souvisí s významem příkazu. Např. příkaz kontrolující, zda trenér nezapomněl uzavřít trénink se nachází v aplikaci :ref:`trainings`. To stejné platí i pro jednořádkové funkce, které volá Cron. Standardně je umisťujeme do vlastního souboru cron.py.

Definice intervalů volání a konkrétních cron jobů se nachází uvnitř aplikace :ref:`vzs` v souboru settings.py jako proměnná ``CRONJOBS``.

Příklad ``CRONJOBS``:

.. code-block:: console

    CRONJOBS = [
        ("0 3 * * *", "features.cron.features_expiry_send_mails"),
        ("0 4 * * *", "one_time_events.cron.unclosed_one_time_events_send_mails"),
        ("0 5 * * *", "trainings.cron.unclosed_trainings_send_mails"),
    ]

Příklad ``features.cron.features_expiry_send_mails``

.. code-block:: python

    def features_expiry_send_mails():
        call_command("send_feature_expiry_mail")