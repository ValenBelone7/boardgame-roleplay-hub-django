from rest_framework import status
from rest_framework.test import APITestCase

from usuarios.models import Usuario
from ventas.models import ItemPedido, Pedido

from .models import Categoria, Editorial, Mecanica, Producto, Resena


class ProductoTests(APITestCase):
    def setUp(self):
        self.staff = Usuario.objects.create_user(
            "admin", password="clave-segura-123", is_staff=True
        )
        self.usuario = Usuario.objects.create_user("pepe", password="clave-segura-123")
        self.estrategia = Categoria.objects.create(nombre="Estrategia")
        self.party = Categoria.objects.create(nombre="Party")
        self.devir = Editorial.objects.create(nombre="Devir", pais="España")
        self.comercio = Mecanica.objects.create(nombre="Comercio y negociación")
        self.catan = Producto.objects.create(
            nombre="Catan",
            precio=89900,
            stock=8,
            jugadores_min=3,
            jugadores_max=4,
            categoria=self.estrategia,
            editorial=self.devir,
        )
        self.catan.mecanicas.add(self.comercio)
        self.dixit = Producto.objects.create(
            nombre="Dixit",
            precio=64900,
            stock=7,
            jugadores_min=3,
            jugadores_max=8,
            categoria=self.party,
        )
        self.url = "/api/productos/"
        self.data = {
            "nombre": "Azul",
            "tipo": "JUEGO_MESA",
            "precio": "74900.00",
            "stock": 6,
            "categoria": self.estrategia.id,
        }

    def test_list_productos_sin_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertIn("next", response.data)

    def test_list_anida_y_retrieve_no(self):
        # La consigna pide los anidados solo en el list
        response = self.client.get(self.url, {"search": "catan"})
        producto = response.data["results"][0]
        self.assertEqual(producto["categoria"]["nombre"], "Estrategia")
        self.assertEqual(producto["mecanicas"][0]["nombre"], "Comercio y negociación")

        response = self.client.get(f"{self.url}{self.catan.id}/")
        self.assertEqual(response.data["categoria"], self.estrategia.id)
        self.assertEqual(response.data["mecanicas"], [self.comercio.id])

    def test_create_producto_sin_auth(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_producto_usuario_comun(self):
        self.client.login(username="pepe", password="clave-segura-123")
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_producto_staff(self):
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Producto.objects.count(), 3)

    def test_create_expansion_sin_juego_base(self):
        self.client.login(username="admin", password="clave-segura-123")
        self.data["tipo"] = "EXPANSION"
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("juego_base", response.data)

    def test_create_jugadores_min_mayor_que_max(self):
        self.client.login(username="admin", password="clave-segura-123")
        self.data |= {"jugadores_min": 5, "jugadores_max": 2}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtro_categoria_y_precio(self):
        response = self.client.get(
            self.url, {"categoria": self.estrategia.id, "precio__lte": 90000}
        )
        self.assertEqual([p["nombre"] for p in response.data["results"]], ["Catan"])

        response = self.client.get(self.url, {"precio__lte": 70000})
        self.assertEqual([p["nombre"] for p in response.data["results"]], ["Dixit"])

    def test_filtro_cantidad_de_jugadores(self):
        # Juegos para 6 jugadores
        response = self.client.get(self.url, {"jugadores_min__lte": 6, "jugadores_max__gte": 6})
        self.assertEqual([p["nombre"] for p in response.data["results"]], ["Dixit"])

    def test_busqueda_por_editorial(self):
        response = self.client.get(self.url, {"search": "devir"})
        self.assertEqual([p["nombre"] for p in response.data["results"]], ["Catan"])

    def test_ordenamiento_por_precio(self):
        response = self.client.get(self.url, {"ordering": "precio"})
        self.assertEqual([p["nombre"] for p in response.data["results"]], ["Dixit", "Catan"])

    def test_borrado_logico_staff(self):
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.delete(f"{self.url}{self.catan.id}/borrado_logico/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.catan.refresh_from_db()
        self.assertFalse(self.catan.activo)

        response = self.client.get(self.url, {"activo": "true"})
        self.assertEqual([p["nombre"] for p in response.data["results"]], ["Dixit"])

    def test_borrado_logico_usuario_comun(self):
        self.client.login(username="pepe", password="clave-segura-123")
        response = self.client.delete(f"{self.url}{self.catan.id}/borrado_logico/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_borrar_producto_vendido(self):
        pedido = Pedido.objects.create(usuario=self.usuario)
        ItemPedido.objects.create(pedido=pedido, producto=self.catan, precio_unitario=89900)
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.delete(f"{self.url}{self.catan.id}/")
        # ItemPedido.producto es PROTECT: 400 con el motivo y no 500
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Producto.objects.filter(id=self.catan.id).exists())

    def test_borrar_categoria_con_productos(self):
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.delete(f"/api/categorias/{self.estrategia.id}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResenaTests(APITestCase):
    def setUp(self):
        self.autor = Usuario.objects.create_user("lucia", password="clave-segura-123")
        self.otro = Usuario.objects.create_user("mateo", password="clave-segura-123")
        categoria = Categoria.objects.create(nombre="Estrategia")
        self.catan = Producto.objects.create(nombre="Catan", precio=89900, categoria=categoria)
        self.resena = Resena.objects.create(
            producto=self.catan, usuario=self.autor, puntaje=5, comentario="Excelente"
        )
        self.url = "/api/resenas/"

    def test_list_resenas_sin_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Anida el usuario sin exponer el email
        self.assertEqual(response.data["results"][0]["usuario"]["username"], "lucia")
        self.assertNotIn("email", response.data["results"][0]["usuario"])

    def test_create_resena_sin_auth(self):
        response = self.client.post(self.url, {"producto": self.catan.id, "puntaje": 4})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_resena_usa_el_usuario_logueado(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.post(
            self.url, {"producto": self.catan.id, "puntaje": 4, "usuario": self.autor.id}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["usuario"], self.otro.id)

    def test_create_resena_duplicada(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.post(self.url, {"producto": self.catan.id, "puntaje": 3})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_resena_puntaje_fuera_de_rango(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.post(self.url, {"producto": self.catan.id, "puntaje": 6})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_editar_resena_ajena(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.patch(f"{self.url}{self.resena.id}/", {"puntaje": 1})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editar_resena_propia(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.patch(f"{self.url}{self.resena.id}/", {"puntaje": 4})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["puntaje"], 4)

    def test_resenas_de_un_producto_paginadas(self):
        response = self.client.get(f"/api/productos/{self.catan.id}/resenas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["comentario"], "Excelente")
