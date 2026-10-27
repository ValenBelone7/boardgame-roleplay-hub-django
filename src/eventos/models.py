from django.conf import settings
from django.db import models

from catalogo.models import Producto


class Evento(models.Model):
    TIPOS = [
        ("TORNEO", "Torneo"),
        ("PARTIDA_ROL", "Partida de rol"),
        ("CAMPANA_ROL", "Campaña de rol"),
        ("NOCHE_JUEGOS", "Noche de juegos"),
    ]

    ESTADOS = [
        ("PROGRAMADO", "Programado"),
        ("EN_CURSO", "En curso"),
        ("FINALIZADO", "Finalizado"),
        ("CANCELADO", "Cancelado"),
    ]

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=12, choices=TIPOS, default="TORNEO")
    juego = models.ForeignKey(
        Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name="eventos"
    )
    organizador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="eventos_organizados"
    )
    fecha = models.DateTimeField()
    cupo = models.PositiveSmallIntegerField()
    costo_inscripcion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=ESTADOS, default="PROGRAMADO")

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.nombre} ({self.fecha:%d/%m/%Y})"


class Inscripcion(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="inscripciones")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inscripciones"
    )
    personaje = models.CharField(max_length=100, blank=True)  # en partidas de rol
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha"]
        verbose_name = "inscripción"
        verbose_name_plural = "inscripciones"
        unique_together = ("evento", "usuario")

    def __str__(self):
        return f"{self.usuario} en {self.evento.nombre}"


class Resultado(models.Model):
    # Tabla de ganadores: una fila por puesto en el podio del evento
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="resultados")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resultados"
    )
    posicion = models.PositiveSmallIntegerField()  # 1 = campeón
    puntos = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["evento", "posicion"]
        unique_together = [("evento", "posicion"), ("evento", "usuario")]

    def __str__(self):
        return f"{self.posicion}° — {self.evento.nombre}: {self.usuario}"


class Leyenda(models.Model):
    # Crónica de lo que pasó en la mesa durante un evento
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="leyendas")
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leyendas"
    )
    protagonista = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leyendas_protagonizadas",
    )
    titulo = models.CharField(max_length=150)
    relato = models.TextField()
    destacada = models.BooleanField(default=False)  # la marca el staff
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return self.titulo
