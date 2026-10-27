from django.shortcuts import render
from django.utils import timezone

from catalogo.models import Producto
from eventos.models import Evento, Leyenda


def inicio(request):
    # Vista principal: bienvenida a Arcana con un resumen de la tienda y la comunidad
    proximos_eventos = Evento.objects.filter(
        estado="PROGRAMADO", fecha__gte=timezone.now()
    ).order_by("fecha")

    contexto = {
        "cantidad_productos": Producto.objects.filter(activo=True).count(),
        "cantidad_eventos": proximos_eventos.count(),
        "cantidad_leyendas": Leyenda.objects.count(),
        "proximos_eventos": proximos_eventos.select_related("juego")[:3],
        "leyenda_destacada": Leyenda.objects.filter(destacada=True)
        .select_related("evento", "protagonista")
        .first(),
    }
    return render(request, "inicio.html", contexto)
