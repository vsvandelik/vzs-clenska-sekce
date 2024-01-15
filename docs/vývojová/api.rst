***************************************
API
***************************************

:term:`IS` implementuje REST API pro základní operace s entitami.
Používá k tomu knihovnu `Django REST framework <https://www.django-rest-framework.org/>`_.

---------
Endpointy
---------
API poskytuje operace pro následující entity:

- jednorázové akce - ``/api/one-time``
- osoby - ``/api/persons``
- pozice - ``/api/positions``
- skupiny - ``/api/groups``
- transakce - ``/api/transactions``
- tréninky - ``/api/trainings``
- uživatelé - ``/api/users``
- vlastnosti - ``/api/features``

Tento přehled je také dostupný na ``/api``.

Pro každý typ entity lze získat seznam všech entit daného typu
a přidat novou entitu pomocí HTTP GET a POST požadavků
na endpoint odpovídající typu entity.

Každá entita má svůj endpoint ve tvaru ``/api/<entity-type>/<entity-id>``.
Na tomto endpointu je možné získat informace o dané entitě,
změnit její údaje a smazat ji pomocí HTTP GET, PUT, PATCH a DELETE požadavků.

Pro všechna těla požadavků a odpovědí se používá formát JSON.

Duplicitní osoba
^^^^^^^^^^^^^^^^
API navíc obsahuje jeden endpoint, POST na ``/api/persons/exists``,
který lze použít ke zjištění,
zda existuje v databázi osoba s daným jménem a příjmením.

Tělo požadavku musí obsahovat klíče: ``first_name`` a ``last_name``.
Tělo odpovědi obsahuje pouze boolean hodnotu.

------------------------
Autentizace a autorizace
------------------------
Pro přístup k API je třeba se autentizovat. :term:`IS` k tomu používá dva mechanismy.
Jedním je stejný mechanismus jako při autentizaci do zbytku aplikace,
tedy ověření pomocí Django sessions a cookies. Pro přístup do API přes tento mechanismus
je třeba být administrátorem.

Druhým mechanismem jsou API tokeny.
Vytvářet tokeny mohou administrátoři na ``/api/tokeny/generovat``.
Pro přístup do API je nutné vygenerovaný token přidat do hlavičky každého požadavku jako
``Authorization: Bearer <token>``.

---------------
Příklad použití
---------------
.. code-block:: javascript

    const request = new Request("/api/persons/1/", {
        method: "GET",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    });

    fetch(request)
        .then((response) => response.json())
        .then((response) => {
            console.log(response);
        });

---------
Rozšíření
---------
Pro přidání API rozhraní pro nový typ entity podle vzoru stávajících endpointů,
lze využít mechanismus ViewSetů z knihovny Django REST framework.

Stačí vytvořit novou třídu, která dědí z ``rest_framework.viewsets.ModelViewSet``
a nový serializer například takto::

    class EntitySerializer(ModelSerializer):
        class Meta:
            model = Entity
            fields = "__all__"

    class EntityViewSet(APIPermissionMixin, ModelViewSet):
        queryset = Entity.objects.all()
        serializer_class = EntitySerializer

Pro manuálnější vytvoření endpointu lze dědit z ``rest_framework.views.APIView``::

    class MyView(APIView):
        def get(self, request, format=None):
            return Response(data)
        
        def post(self, request, format=None):
            return Response(data)

Nakonec se endpointy registrují takto::

    router = DefaultRouter()
    router.register("entities", EntityViewSet)
    urlpatterns = [
        path("api/", include(router.urls)),
        path("api/my-view/", MyView.as_view()),
    ]
