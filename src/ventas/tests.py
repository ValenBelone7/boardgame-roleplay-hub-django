from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from catalogo.models import Categoria, Producto
from usuarios.models import Usuario

from .models import ItemPedido, Pedido


class PedidoTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("lucia", password="clave-segura-123")
        self.otro = Usuario.objects.create_user("mateo", password="clave-segura-123")
        self.staff = Usuario.objects.create_user(
            "admin", password="clave-segura-123", is_staff=True
        )
        categoria = Categoria.objects.create(nombre="Estrategia")
        self.catan = Producto.objects.create(
            nombre="Catan", precio=Decimal(89900), stock=5, categoria=categoria
        )
        self.dados = Producto.objects.create(
            nombre="Dados", precio=Decimal(9900), stock=10, categoria=categoria
        )
        self.pedido = Pedido.objects.create(usuario=self.usuario)
        ItemPedido.objects.create(
            pedido=self.pedido, producto=self.catan, cantidad=1, precio_unitario=89900
        )
        ItemPedido.objects.create(
            pedido=self.pedido, producto=self.dados, cantidad=3, precio_unitario=9900
        )
        self.url = "/api/pedidos/"

    def confirmar(self):
        return self.client.post(f"{self.url}{self.pedido.id}/confirmar/")

    def test_list_pedidos_sin_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_anida_items_con_subtotal(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.get(self.url)
        items = response.data["results"][0]["items"]
        self.assertEqual(items[0]["producto"]["nombre"], "Catan")
        self.assertEqual(items[1]["subtotal"], "29700.00")

    def test_create_pedido(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["usuario"], self.otro.id)
        self.assertEqual(response.data["estado"], "PENDIENTE")

    def test_create_segundo_pedido_pendiente(self):
        # El pedido pendiente funciona como carrito: uno solo por usuario
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_no_ve_pedido_ajeno(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 0)
        response = self.client.get(f"{self.url}{self.pedido.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.confirmar()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_ve_todos_los_pedidos(self):
        Pedido.objects.create(usuario=self.otro)
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.get(self.url)
        self.assertEqual(response.data["count"], 2)

    def test_pedido_no_se_edita_ni_se_borra(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.patch(f"{self.url}{self.pedido.id}/", {"estado": "CONFIRMADO"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.delete(f"{self.url}{self.pedido.id}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_confirmar_descuenta_stock_y_calcula_total(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.confirmar()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "CONFIRMADO")
        self.assertEqual(Decimal(response.data["total"]), Decimal(119600))
        self.assertIsNotNone(response.data["fecha_confirmacion"])
        self.catan.refresh_from_db()
        self.dados.refresh_from_db()
        self.assertEqual(self.catan.stock, 4)
        self.assertEqual(self.dados.stock, 7)

    def test_confirmar_sin_stock(self):
        self.catan.stock = 0
        self.catan.save()
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.confirmar()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Catan", response.data["error"])
        # No se descontó nada de ningún producto
        self.dados.refresh_from_db()
        self.pedido.refresh_from_db()
        self.assertEqual(self.dados.stock, 10)
        self.assertEqual(self.pedido.estado, "PENDIENTE")

    def test_confirmar_pedido_vacio(self):
        self.pedido.items.all().delete()
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.confirmar()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirmar_dos_veces(self):
        self.client.login(username="lucia", password="clave-segura-123")
        self.confirmar()
        response = self.confirmar()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.catan.refresh_from_db()
        self.assertEqual(self.catan.stock, 4)

    def test_cancelar_repone_stock(self):
        self.client.login(username="lucia", password="clave-segura-123")
        self.confirmar()
        response = self.client.post(f"{self.url}{self.pedido.id}/cancelar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "CANCELADO")
        self.catan.refresh_from_db()
        self.assertEqual(self.catan.stock, 5)

    def test_cancelar_dos_veces(self):
        self.client.login(username="lucia", password="clave-segura-123")
        self.client.post(f"{self.url}{self.pedido.id}/cancelar/")
        response = self.client.post(f"{self.url}{self.pedido.id}/cancelar/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ItemPedidoTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user("lucia", password="clave-segura-123")
        self.otro = Usuario.objects.create_user("mateo", password="clave-segura-123")
        categoria = Categoria.objects.create(nombre="Estrategia")
        self.catan = Producto.objects.create(
            nombre="Catan", precio=Decimal(89900), stock=5, categoria=categoria
        )
        self.pedido = Pedido.objects.create(usuario=self.usuario)
        self.url = "/api/items-pedido/"
        self.client.login(username="lucia", password="clave-segura-123")

    def test_agregar_item_copia_el_precio(self):
        response = self.client.post(
            self.url, {"pedido": self.pedido.id, "producto": self.catan.id, "cantidad": 2}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["precio_unitario"], "89900.00")

    def test_agregar_item_cantidad_cero(self):
        response = self.client.post(
            self.url, {"pedido": self.pedido.id, "producto": self.catan.id, "cantidad": 0}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agregar_producto_repetido(self):
        data = {"pedido": self.pedido.id, "producto": self.catan.id, "cantidad": 1}
        self.client.post(self.url, data)
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agregar_producto_inactivo(self):
        self.catan.activo = False
        self.catan.save()
        response = self.client.post(
            self.url, {"pedido": self.pedido.id, "producto": self.catan.id, "cantidad": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_agregar_item_a_pedido_ajeno(self):
        ajeno = Pedido.objects.create(usuario=self.otro)
        response = self.client.post(
            self.url, {"pedido": ajeno.id, "producto": self.catan.id, "cantidad": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ajeno.items.exists())

    def test_modificar_item_de_pedido_confirmado(self):
        item = ItemPedido.objects.create(
            pedido=self.pedido, producto=self.catan, cantidad=1, precio_unitario=89900
        )
        self.pedido.estado = "CONFIRMADO"
        self.pedido.save()
        response = self.client.patch(f"{self.url}{item.id}/", {"cantidad": 3})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(f"{self.url}{item.id}/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
