from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)  # Estrategia, Party, Rol...
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Editorial(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    pais = models.CharField(max_length=60)
    sitio_web = models.URLField(blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "editoriales"

    def __str__(self):
        return self.nombre


class Disenador(models.Model):
    nombre = models.CharField(max_length=100)
    nacionalidad = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "diseñador"
        verbose_name_plural = "diseñadores"

    def __str__(self):
        return self.nombre


class Mecanica(models.Model):
    nombre = models.CharField(max_length=80, unique=True)  # Draft, Deckbuilding, Narrativa...
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "mecánica"
        verbose_name_plural = "mecánicas"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    TIPOS = [
        ("JUEGO_MESA", "Juego de mesa"),
        ("JUEGO_ROL", "Juego de rol"),
        ("EXPANSION", "Expansión"),
        ("ACCESORIO", "Accesorio"),
    ]

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS, default="JUEGO_MESA")
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    # Datos de juego: quedan vacíos en los accesorios
    jugadores_min = models.PositiveSmallIntegerField(null=True, blank=True)
    jugadores_max = models.PositiveSmallIntegerField(null=True, blank=True)
    duracion_minutos = models.PositiveSmallIntegerField(null=True, blank=True)
    edad_minima = models.PositiveSmallIntegerField(null=True, blank=True)
    imagen_url = models.URLField(blank=True)
    activo = models.BooleanField(default=True)  # borrado lógico
    fecha_alta = models.DateTimeField(auto_now_add=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="productos")
    editorial = models.ForeignKey(
        Editorial, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos"
    )
    mecanicas = models.ManyToManyField(Mecanica, blank=True, related_name="productos")
    disenadores = models.ManyToManyField(Disenador, blank=True, related_name="productos")
    # Solo para expansiones: el juego al que pertenecen
    juego_base = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="expansiones"
    )

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class Resena(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="resenas")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resenas"
    )
    puntaje = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "reseña"
        verbose_name_plural = "reseñas"
        unique_together = ("producto", "usuario")  # una reseña por usuario por juego

    def __str__(self):
        return f"{self.producto.nombre} - {self.usuario} ({self.puntaje}/5)"
