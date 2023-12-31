***************************************
Konvence
***************************************
Na této stránce rozvedeme jednotlivé konvence, které jsou dodržovány.

----------------
Jmenné konvence
----------------
Následující tabulka shrnuje jmenné konvence, které jsou používány a doporučujeme se jich držet i v nadcházejícím vývoji.

.. list-table::
   :widths: 25 25
   :header-rows: 1

   * - Týká se
     - Typ konvence
   * - Python souborů
     - `PEP 8 <https://peps.python.org/pep-0008>`_
   * - JS názvů
     - camelCase
   * - HTML id atributů
     - kebab-case

U HTML id atributů platí výjimka pro prvky automaticky generované Djangem při použití formulářů. Django pro atribut id používá konvenci snake_case, kterou jsme se rozhodli ponechat. To umožňuje rozpoznat, zda se jedná o automaticky generovaný prvek, či nikoliv.


-----------------
Formátování kódu
-----------------
Pro formátování kódu se používá Black Code Formatter, soubory HTML/CSS/JS jsou formátovány pomocí djhtml, které umí formátovat Jinja kód. 