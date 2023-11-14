High-level architektura
=======================

Zde je prozatím osnova toho, jak by tento dokument měl vypadat.

- cílová skupina
- backend `Django`
- frontend používající šablonu

# Backend

- `Django`
- rozdělení na jednotlivé aplikace

## Databáze

- `Django` ORM
- PostgreSQL
- automatické migracie
- každá aplikace má své modely
- polymorfní modely z `django-polymorphic`

## Šablony

- `Django`
- vlastní filtry a tagy

## Formuláře

- validace - `Django`
- zobrazování - `django-crispy-forms`

## Popis aplikací

### `users`

#### Autentifikace

- `Django` *session*, email + heslo, případně Google OAuth2

#### Autorizace

- `Django` `Permission`
- filtry `perm_url` a `ifperm`

#### Aktivní osoba

- `Django` *session*

### `transactions`

- generování QR - `api.paylibo.com` API
- integrace s FIO bankou

### `api`

- REST API skrze `djangorestframework`
- autentifikace - token či `users` autentifikace
- CRUD pro základní modely

### ...

# Frontend

## Základní komponenty

- `Bootstrap`
- `AdminLTE`
- `Font Awesome`

## Tabulky

- `datatables`

## Modální okna

- styl z `Bootstrap`
- HTML obsah získaný přes JS `fetch`

# Development

- `GitHub Actions` - testování spuštění a migrací, deployment
- `pre-commmit` - formátování
