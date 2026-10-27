from rest_framework import status
from rest_framework.test import APITestCase

from .models import Usuario


class RegistroTests(APITestCase):
    def setUp(self):
        self.url = "/api/usuarios/registro/"
        self.data = {
            "username": "lucia",
            "email": "lucia@arcana.example",
            "password": "clave-segura-123",
            "alias": "Lu la Estratega",
        }

    def test_registro_sin_auth(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["alias"], "Lu la Estratega")
        self.assertNotIn("password", response.data)

    def test_registro_hashea_la_contrasena(self):
        self.client.post(self.url, self.data)
        usuario = Usuario.objects.get(username="lucia")
        self.assertNotEqual(usuario.password, "clave-segura-123")
        self.assertTrue(usuario.check_password("clave-segura-123"))

    def test_registro_usuario_repetido(self):
        self.client.post(self.url, self.data)
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_contrasena_corta(self):
        self.data["password"] = "1234"
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_y_token_jwt(self):
        # Flujo del frontend: registrarse, pedir el token y usarlo con Bearer
        self.client.post(self.url, self.data)
        response = self.client.post(
            "/api/token/", {"username": "lucia", "password": "clave-segura-123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        response = self.client.get("/api/usuarios/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "lucia")


class UsuarioTests(APITestCase):
    def setUp(self):
        self.staff = Usuario.objects.create_user(
            "admin", email="admin@arcana.example", password="clave-segura-123", is_staff=True
        )
        self.usuario = Usuario.objects.create_user(
            "mateo", email="mateo@arcana.example", password="clave-segura-123"
        )

    def test_me_sin_auth(self):
        response = self.client.get("/api/usuarios/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_con_sesion(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.get("/api/usuarios/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "mateo@arcana.example")

    def test_list_usuarios_sin_auth(self):
        response = self.client.get("/api/usuarios/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_usuarios_comun_no_ve_emails(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.get("/api/usuarios/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertNotIn("email", response.data["results"][0])

    def test_list_usuarios_staff_ve_emails(self):
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.get("/api/usuarios/")
        self.assertIn("email", response.data["results"][0])
