from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    # Nombre de jugador que se muestra en la tabla de ganadores y en las leyendas
    alias = models.CharField(max_length=50, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.alias or self.username
