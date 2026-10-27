from django.contrib import admin

from .models import Evento, Inscripcion, Leyenda, Resultado


class InscripcionInline(admin.TabularInline):
    model = Inscripcion
    extra = 0


class ResultadoInline(admin.TabularInline):
    model = Resultado
    extra = 0
    ordering = ["posicion"]


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tipo", "juego", "fecha", "cupo", "estado", "organizador"]
    list_filter = ["tipo", "estado", "fecha"]
    search_fields = ["nombre", "juego__nombre", "organizador__username"]
    ordering = ["-fecha"]
    date_hierarchy = "fecha"
    inlines = [InscripcionInline, ResultadoInline]


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ["evento", "usuario", "personaje", "fecha"]
    list_filter = ["evento"]
    search_fields = ["usuario__username", "usuario__alias", "personaje", "evento__nombre"]


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ["evento", "posicion", "usuario", "puntos"]
    list_filter = ["evento", "posicion"]
    search_fields = ["usuario__username", "usuario__alias", "evento__nombre"]
    ordering = ["evento", "posicion"]


@admin.register(Leyenda)
class LeyendaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "evento", "autor", "protagonista", "destacada", "fecha"]
    list_filter = ["destacada", "evento"]
    search_fields = ["titulo", "relato", "autor__username", "protagonista__username"]
    ordering = ["-fecha"]
    list_editable = ["destacada"]
