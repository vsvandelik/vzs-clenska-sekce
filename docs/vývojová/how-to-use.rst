***************************************
Jak použít
***************************************
Tato stránka obsahuje návody a ukázky kódu demonstrující použití běžných primitiv, které se často opakovaně vyskytují napříč všemi aplikacemi.


.. _Bootstrap_modals_example:

-------------------------
Modální okna Bootstrapu
-------------------------



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