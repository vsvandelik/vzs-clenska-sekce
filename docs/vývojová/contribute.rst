***************************************
Jak přispět
***************************************

Rádi bychom Vám vyjádřili své díky za to, že alespoň zvažujete přispět a zlepšit tak chod :term:`Organizace`.

Pokud více o nějaké chybě, máte nějaký námět na zlepšení neváhejte a kontaktujte správce Vojtu Švandelíka. 

Pokud rozumíte Pythonu, Djangu a rádi byste něco vylepšili sami, tak se domluvte s Vojtou Švandelíkem. Repozitář se zdrojovým kódem se nachází na GitHubu a momentálně je nastaven jako privátní. Po domluvě je možné získat přístup ke zdrojovému kódu. Bližší informace o licenci SW díla se nachází v sekci :doc:`../license`.

----------------------
Workflow
----------------------

1. Domluvte se Vojtou Švandelíkem na konkrétní funkcionalitě, kterou budete implentovat. Pro tuto funkcionalitu se vytvoří samostatný GitHub issue.

2. Naklonujte si repozitář ``git@github.com:vsvandelik/vzs-clenska-sekce.git``. Můžete využít příkaz ``git clone git@github.com:vsvandelik/vzs-clenska-sekce.git``

3. Vytvořte branch ve formátu ``číslo_issue-nazev-issue-s-pomlckami``. Příklad: Issue bylo přiděleno číslo 784, jeho název je ``Uzavření tréninku selže a vrátí exception xyz``, název branch potom bude ``784-uzavreni-treninku-selze-a-vrati-exception-xyz``. Branch můžete vytvořit a změnit příkazem ``git checkout -b 784-uzavreni-treninku-selze-a-vrati-exception-xyz``.

4. Spusťte příkaz ``pre-commit install`` z adresáře repozitáře. Tento příkaz zajistí, že se s Vašemi commity kód naformátuje dle vyžadovaných standardů.

5. Proveďte implementaci a průběžně provádějte commity.

6. Před otevřením PR proveďte spojení všech Vašich commitů do jednoho, můžete použít např. příkaz ``git rebase -i HEAD~n``, kde ``n`` je počet commitů, které chcete spojit do jednoho.

7. Otevřte PR na GitHubu a počkejte na review.

8. Upravte Váš kód dle požadavků. (Přidejte další commity do stejné branch).

9. Správce provede merge do master branch.
