***************************************
Jak přispět
***************************************

Rádi bychom vám vyjádřili své díky za to, že alespoň zvažujete přispět a zlepšit tak chod :term:`Organizace`.

Pokud víte o nějaké chybě, máte nějaký námět na zlepšení neváhejte a kontaktujte správce Vojtěcha Švandelíka.

Pokud rozumíte Pythonu, Djangu a rádi byste něco vylepšili sami, tak se domluvte s Vojtěchem Švandelíkem. Repozitář se zdrojovým kódem se nachází na GitHubu a momentálně je nastaven jako privátní. Po domluvě je možné získat přístup ke zdrojovému kódu. Bližší informace o licenci SW díla se nachází v sekci :doc:`../license`.


.. _workflow:

----------------------
Workflow
----------------------

Potřebujete mít v počítači nainstalované následující závislosti:

- git nastavený pro přístup na GitHub, `návod <https://docs.github.com/en/get-started/quickstart/set-up-git>`_
- Python ≥ 3.11 
- Node.js ≥ 17.0.0

Poté můžete pokračovat dle návodu:

1. Domluvte se Vojtěchem Švandelíkem na konkrétní funkcionalitě, kterou budete implentovat. Pro tuto funkcionalitu se vytvoří samostatný GitHub issue.

2. Naklonujte si repozitář ``git@github.com:vsvandelik/vzs-clenska-sekce.git``.

3. Změňte aktuální cestu do adresáře repozitáře.

4. Vytvořte si virtuální prostředí příkazem ``python -m venv venv``

5. Aktivujte virtuální prostředí příkazem

.. code-block:: console

    source venv/bin/activate  (Linux)

    venv\Scripts\activate.bat  (Windows)

6. Nainstalujte si všechny potřebné závislosti.

.. code-block:: console

    pip install -r requirements.txt
    pip install -r requirements_dev.txt
    npm install

7. Vytvořte branch ve formátu ``číslo_issue-nazev-issue-s-pomlckami``. Příklad: Issue bylo přiděleno číslo 784, jeho název je ``Uzavření tréninku selže a vrátí exception xyz``, název branch potom bude ``784-uzavreni-treninku-selze-a-vrati-exception-xyz``. Branch můžete vytvořit a změnit příkazem ``git checkout -b 784-uzavreni-treninku-selze-a-vrati-exception-xyz``.

8. Spusťte příkaz ``pre-commit install`` z adresáře repozitáře. Tento příkaz zajistí, že se s vašemi commity kód naformátuje dle vyžadovaných standardů.

9. Proveďte implementaci a průběžně provádějte commity.

10. Před otevřením PR proveďte spojení všech vašich commitů do jednoho, můžete použít např. příkaz ``git rebase -i HEAD~n``, kde ``n`` je počet commitů, které chcete spojit do jednoho.

11. Otevřete PR na GitHubu a počkejte na review.

12. Upravte váš kód dle požadavků. (Přidejte další commity do stejné branch).

13. Správce provede merge do master branch.

.. _dokumentace:
----------------------
Dokumentace
----------------------
Dokumentace, kterou právě čtete, je součástí projektu stejně jako zdrojový kód :term:`IS`. Po přípravě prostředí popsaného v předchozí části :ref:`workflow`, je možné provést sestavení dokumentace spuštěním následujících příkazů z adresáře :ref:`docs/`.

.. code-block:: console

    sphinx-apidoc -o _autodoc ..
    make html


Dokumentace se skládá pouze ze statických stránek, pro lokální prohlížení stačí otevřít soubor docs/_build/html/index.html v libovolném webovém prohlížeči.

Licence i postup pro úpravu dokumentace je stejný jako v případě úprav zdrojového kódu. Vždy je potřeba se předem domluvit na konkrétní úpravě, na kterou se vytvoří vlastní issue na GitHubu.