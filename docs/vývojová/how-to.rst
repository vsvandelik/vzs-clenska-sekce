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
Rozmyslíme se id modálního okna, které budeme vytvářet v dalším kroku. Definujeme ho jako ``"unenroll-myself-participant-modal"``. Modální okno bude zobrazovat odpověď požadavku z akce ``{% url 'events:unenroll-myself-participant' active_person_enrollment.id %}``, která je dobře definována.

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

.. code-block:: console

    registerModal("unenroll-myself-participant-modal")


.. _DataTable_example:

-------------------------
DataTables
-------------------------
Na existující tabulku s ``id="tokens-table"`` je možné DataTables aplikovat použitím funkce ``datatableEnable(id, searchableColumns, orderableColumns, order = [])``, nebo ``simpleOrderableTableEnable(id, orderableColumns, order = [])``. Druhá funkce skryje vyhledávací pole. Parametry ``searchableColumns`` a ``orderableColumns`` očekávají pole indexů sloupců. První parametr definuje sloupce, přes které se vyhledává při použití vyhledávacího pole. Druhý parametr definuje sloupce, které je možné řadit. Konečně parametr order definuje pořadí sloupců, tento parametr může být vynechán, pokud není potřeba měnit pořadí sloupců.

Příklad použití:

.. code-block:: console

    {% block scripts %}
        <script src="{% static "datatables.js" %}"></script>
        <script>datatableEnable("tokens-table", [0, 1], [0, 1, 2]);</script>
    {% endblock %}

-------------------------------
 Select2
-------------------------------
Pokud vytvoříme formulářové pole, které bude mít na výběr více položek. Django použije jako widget k renderování buďto radio button nebo select box v závislosti na počtu položek. Pokud chceme definovat použití Select2, musíme explicitně nastavit widget.

Příklad: Máme formulář s jedním políčkem ``"group"``, u kterého vynutíme použití Select2.

.. code-block:: console

    class GroupMembershipForm(ModelForm):
    class Meta:
        fields = ["group"]
        widgets = {
            "group": Select2Widget(),
        }

-------------------------------
 Funkce volané daemonem Cron
-------------------------------

------------------------------------
 Vytvoření vlastního Django příkazu
------------------------------------