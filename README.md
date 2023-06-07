# Členská sekce vodní záchranné služby Praha 15
## Informace k Black Code Formatter
* Před prací se zdrojovým kódem je nutné nainstalovat závislosti z `requirements_dev.txt`
* Po provedení `git clone` je nutné spustit příkaz `pre-commit install`, který aktivuje hook pro automatické formátování kódu před příkazem `git commit`
* Pokud hook Black Code Formatteru doběhne s chybou, je to v pořádku. Chybu je možné ignorovat, jenom je nutné znovu provést `git add` a `git commit`, následně je možné provést `git push`