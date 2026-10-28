from django.contrib import admin

from .models import Categoria, Disenador, Editorial, Mecanica, Producto, Resena

admin.site.site_header = "Arcana — Administración"
admin.site.site_title = "Arcana"
admin.site.index_title = "Tienda, eventos y salón de la fama"


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion"]
    search_fields = ["nombre"]


@admin.register(Editorial)
class EditorialAdmin(admin.ModelAdmin):
    list_display = ["nombre", "pais", "sitio_web"]
    list_filter = ["pais"]
    search_fields = ["nombre", "pais"]


@admin.register(Disenador)
class DisenadorAdmin(admin.ModelAdmin):
    list_display = ["nombre", "nacionalidad"]
    list_filter = ["nacionalidad"]
    search_fields = ["nombre"]


@admin.register(Mecanica)
class MecanicaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion"]
    search_fields = ["nombre"]


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tipo", "categoria", "editorial", "precio", "stock", "activo"]
    list_filter = ["tipo", "categoria", "editorial", "activo", "mecanicas"]
    search_fields = ["nombre", "editorial__nombre", "disenadores__nombre"]
    ordering = ["nombre"]
    list_editable = ["precio", "stock", "activo"]
    filter_horizontal = ["mecanicas", "disenadores"]
    autocomplete_fields = ["juego_base"]


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ["producto", "usuario", "puntaje", "fecha"]
    list_filter = ["puntaje", "fecha"]
    search_fields = ["producto__nombre", "usuario__username", "comentario"]
    ordering = ["-fecha"]
