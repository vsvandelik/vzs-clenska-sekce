# Členská sekce vodní záchranné služby Praha 15

## Informace k pre-commit hooks

-   Před prací se zdrojovým kódem je nutné nainstalovat závislosti z `requirements_dev.txt`
-   Po provedení `git clone` je nutné spustit příkaz `pre-commit install`, který aktivuje hook pro automatické formátování kódu, které se provádí s příkazem `git commit`, před provedením commitu
-   Pokud hooky doběhnou s chybou, je to v pořádku. Chybu je možné ignorovat, jenom je nutné znovu provést `git add` a `git commit`, následně je možné provést `git push`
- Manuálně spustit všechny hooks je možné provedením příkazu `pre-commit run --all-files`

### djhtml a Windows
Je potřeba nastavit Systémovou proměnnou `PYTHONUTF8=1`. To je možné přes GUI "Edit the system environment variables" nebo v příkazové řádce, která musí být spuštěna jako správce, příkazem `setx /m PYTHONUTF8 1`. Jinak to nefunguje a píše nějaké errory s Unicode a neznámými znaky.

## Informace k front-endu

- Pro zprovoznění frontendových závislostí je třeba mít nainstalované `node.js` a zavolat příkaz `npm install`, který nainstaluje závislosti vydefinované v souboru `package.json`.

## Generovani dokumentace

Ve slozce `docs`:

```
sphinx-apidoc -o _autodoc ..
make html
```