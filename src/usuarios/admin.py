from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ["username", "alias", "email", "first_name", "last_name", "is_staff"]
    search_fields = ["username", "alias", "email", "first_name", "last_name"]
    fieldsets = UserAdmin.fieldsets + (("Jugador", {"fields": ("alias", "fecha_nacimiento")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Jugador", {"fields": ("alias", "fecha_nacimiento")}),
    )
