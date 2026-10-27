from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from catalogo.models import Categoria, Producto
from usuarios.models import Usuario

from .models import Evento, Inscripcion, Leyenda, Resultado


class EventoTests(APITestCase):
    def setUp(self):
        self.staff = Usuario.objects.create_user(
            "admin", password="clave-segura-123", is_staff=True
        )
        self.lucia = Usuario.objects.create_user("lucia", password="clave-segura-123")
        self.mateo = Usuario.objects.create_user("mateo", password="clave-segura-123")
        categoria = Categoria.objects.create(nombre="Estrategia")
        self.catan = Producto.objects.create(nombre="Catan", precio=89900, categoria=categoria)
        self.torneo = Evento.objects.create(
            nombre="Torneo de Catan",
            tipo="TORNEO",
            juego=self.catan,
            organizador=self.staff,
            fecha=timezone.now() + timedelta(days=7),
            cupo=2,
        )
        self.url = "/api/eventos/"

    def inscribirse(self, evento=None, **data):
        evento = evento or self.torneo
        return self.client.post(f"{self.url}{evento.id}/inscribirse/", data)

    def test_list_eventos_sin_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        evento = response.data["results"][0]
        self.assertEqual(evento["juego"]["nombre"], "Catan")
        self.assertEqual(evento["organizador"]["username"], "admin")
        self.assertEqual(evento["inscriptos"], 0)

    def test_retrieve_no_anida(self):
        response = self.client.get(f"{self.url}{self.torneo.id}/")
        self.assertEqual(response.data["juego"], self.catan.id)

    def test_filtro_por_estado(self):
        response = self.client.get(self.url, {"estado": "FINALIZADO"})
        self.assertEqual(response.data["count"], 0)
        response = self.client.get(self.url, {"estado": "PROGRAMADO"})
        self.assertEqual(response.data["count"], 1)

    def test_create_evento_usuario_comun(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.post(self.url, {"nombre": "Mi torneo"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_evento_staff(self):
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.post(
            self.url,
            {
                "nombre": "Noche de juegos",
                "tipo": "NOCHE_JUEGOS",
                "organizador": self.lucia.id,
                "fecha": (timezone.now() + timedelta(days=3)).isoformat(),
                "cupo": 20,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # El organizador es el staff logueado aunque el body diga otra cosa
        self.assertEqual(response.data["organizador"], self.staff.id)

    def test_inscribirse_sin_auth(self):
        response = self.inscribirse()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inscribirse(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.inscribirse(personaje="Lyra, maga elfa")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["usuario"], self.lucia.id)
        self.assertEqual(response.data["personaje"], "Lyra, maga elfa")

    def test_inscribirse_dos_veces(self):
        self.client.login(username="lucia", password="clave-segura-123")
        self.inscribirse()
        response = self.inscribirse()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.torneo.inscripciones.count(), 1)

    def test_inscribirse_sin_cupo(self):
        self.torneo.cupo = 1
        self.torneo.save()
        Inscripcion.objects.create(evento=self.torneo, usuario=self.mateo)
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.inscribirse()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inscribirse_a_evento_finalizado(self):
        self.torneo.estado = "FINALIZADO"
        self.torneo.save()
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.inscribirse()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_podio_ordenado(self):
        Resultado.objects.create(evento=self.torneo, usuario=self.mateo, posicion=2, puntos=7)
        Resultado.objects.create(evento=self.torneo, usuario=self.lucia, posicion=1, puntos=10)
        response = self.client.get(f"{self.url}{self.torneo.id}/podio/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([r["usuario"]["username"] for r in response.data], ["lucia", "mateo"])
        self.assertNotIn("email", response.data[0]["usuario"])


class InscripcionTests(APITestCase):
    def setUp(self):
        staff = Usuario.objects.create_user("admin", password="clave-segura-123", is_staff=True)
        self.lucia = Usuario.objects.create_user("lucia", password="clave-segura-123")
        self.mateo = Usuario.objects.create_user("mateo", password="clave-segura-123")
        self.evento = Evento.objects.create(
            nombre="Campaña de D&D",
            tipo="CAMPANA_ROL",
            organizador=staff,
            fecha=timezone.now() + timedelta(days=7),
            cupo=5,
        )
        self.inscripcion = Inscripcion.objects.create(evento=self.evento, usuario=self.lucia)
        self.url = f"/api/inscripciones/{self.inscripcion.id}/"

    def test_create_por_post_no_permitido(self):
        # Las inscripciones se crean solo con eventos/{id}/inscribirse/
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.post("/api/inscripciones/", {"evento": self.evento.id})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_baja_de_inscripcion_ajena(self):
        self.client.login(username="mateo", password="clave-segura-123")
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_baja_de_inscripcion_propia(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Inscripcion.objects.exists())

    def test_baja_con_evento_en_curso(self):
        self.evento.estado = "EN_CURSO"
        self.evento.save()
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ResultadoTests(APITestCase):
    def setUp(self):
        self.staff = Usuario.objects.create_user(
            "admin", password="clave-segura-123", is_staff=True
        )
        self.lucia = Usuario.objects.create_user("lucia", password="clave-segura-123")
        self.mateo = Usuario.objects.create_user("mateo", password="clave-segura-123")
        self.sofia = Usuario.objects.create_user("sofia", password="clave-segura-123")
        Usuario.objects.create_user("nicolas", password="clave-segura-123")  # nunca jugó
        eventos = [
            Evento.objects.create(
                nombre=f"Torneo {n}",
                organizador=self.staff,
                fecha=timezone.now() - timedelta(days=n),
                cupo=8,
                estado="FINALIZADO",
            )
            for n in range(1, 4)
        ]
        # lucia: 2 títulos; mateo: 1 título y más puntos que sofia; sofia: sin títulos
        for evento, podio in zip(
            eventos,
            [
                [(self.lucia, 10), (self.mateo, 7)],
                [(self.lucia, 10), (self.sofia, 7)],
                [(self.mateo, 10), (self.sofia, 7)],
            ],
            strict=True,
        ):
            for posicion, (usuario, puntos) in enumerate(podio, start=1):
                Inscripcion.objects.create(evento=evento, usuario=usuario)
                Resultado.objects.create(
                    evento=evento, usuario=usuario, posicion=posicion, puntos=puntos
                )
        self.evento = eventos[0]  # podio: lucia 1°, mateo 2°

    def test_salon_de_la_fama(self):
        response = self.client.get("/api/resultados/salon_de_la_fama/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ranking = [(u["username"], u["titulos"], u["puntos"]) for u in response.data["results"]]
        # nicolas no subió nunca al podio, así que no aparece
        self.assertEqual(ranking, [("lucia", 2, 20), ("mateo", 1, 17), ("sofia", 0, 14)])

    def test_cargar_resultado_usuario_comun(self):
        self.client.login(username="lucia", password="clave-segura-123")
        response = self.client.post(
            "/api/resultados/",
            {"evento": self.evento.id, "usuario": self.lucia.id, "posicion": 3},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cargar_resultado_inscripto(self):
        Inscripcion.objects.create(evento=self.evento, usuario=self.sofia)
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.post(
            "/api/resultados/",
            {"evento": self.evento.id, "usuario": self.sofia.id, "posicion": 3, "puntos": 5},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cargar_resultado_no_inscripto(self):
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.post(
            "/api/resultados/",
            {"evento": self.evento.id, "usuario": self.sofia.id, "posicion": 3},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("usuario", response.data)

    def test_cargar_puesto_repetido(self):
        Inscripcion.objects.create(evento=self.evento, usuario=self.sofia)
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.post(
            "/api/resultados/",
            {"evento": self.evento.id, "usuario": self.sofia.id, "posicion": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("usuario", response.data)

    def test_cambiar_resultado_a_no_inscripto(self):
        resultado = Resultado.objects.get(evento=self.evento, posicion=2)
        self.client.login(username="admin", password="clave-segura-123")
        response = self.client.patch(f"/api/resultados/{resultado.id}/", {"usuario": self.sofia.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LeyendaTests(APITestCase):
    def setUp(self):
        staff = Usuario.objects.create_user("admin", password="clave-segura-123", is_staff=True)
        self.autor = Usuario.objects.create_user("sofia", password="clave-segura-123")
        self.nico = Usuario.objects.create_user("nicolas", password="clave-segura-123")
        self.evento = Evento.objects.create(
            nombre="Campaña de D&D",
            organizador=staff,
            fecha=timezone.now() - timedelta(days=1),
            cupo=5,
            estado="EN_CURSO",
        )
        self.leyenda = Leyenda.objects.create(
            evento=self.evento,
            autor=self.autor,
            protagonista=self.nico,
            titulo="El bardo y el dragón verde",
            relato="Un 19 natural en Persuasión.",
        )
        self.url = "/api/leyendas/"

    def test_list_leyendas_sin_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["protagonista"]["username"], "nicolas")

    def test_busqueda_en_el_relato(self):
        response = self.client.get(self.url, {"search": "persuasión"})
        self.assertEqual(response.data["count"], 1)
        response = self.client.get(self.url, {"search": "catan"})
        self.assertEqual(response.data["count"], 0)

    def test_create_leyenda(self):
        self.client.login(username="nicolas", password="clave-segura-123")
        response = self.client.post(
            self.url,
            {
                "evento": self.evento.id,
                "titulo": "Un pícaro y un cofre",
                "relato": "El cofre tenía trampa.",
                "destacada": True,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["autor"], self.nico.id)
        # Solo el staff destaca leyendas (desde el admin)
        self.assertFalse(response.data["destacada"])

    def test_create_leyenda_de_evento_programado(self):
        self.evento.estado = "PROGRAMADO"
        self.evento.save()
        self.client.login(username="nicolas", password="clave-segura-123")
        response = self.client.post(
            self.url,
            {"evento": self.evento.id, "titulo": "Spoiler", "relato": "Todavía no pasó."},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("evento", response.data)

    def test_editar_leyenda_ajena(self):
        self.client.login(username="nicolas", password="clave-segura-123")
        response = self.client.patch(f"{self.url}{self.leyenda.id}/", {"titulo": "Otro"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
