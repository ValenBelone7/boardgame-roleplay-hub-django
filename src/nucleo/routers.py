from rest_framework.routers import DefaultRouter

from catalogo.views import (
    CategoriaViewSet,
    DisenadorViewSet,
    EditorialViewSet,
    MecanicaViewSet,
    ProductoViewSet,
    ResenaViewSet,
)
from eventos.views import EventoViewSet, InscripcionViewSet, LeyendaViewSet, ResultadoViewSet
from usuarios.views import UsuarioViewSet
from ventas.views import ItemPedidoViewSet, PedidoViewSet

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuarios")
router.register("categorias", CategoriaViewSet, basename="categorias")
router.register("editoriales", EditorialViewSet, basename="editoriales")
router.register("disenadores", DisenadorViewSet, basename="disenadores")
router.register("mecanicas", MecanicaViewSet, basename="mecanicas")
router.register("productos", ProductoViewSet, basename="productos")
router.register("resenas", ResenaViewSet, basename="resenas")
router.register("pedidos", PedidoViewSet, basename="pedidos")
router.register("items-pedido", ItemPedidoViewSet, basename="items-pedido")
router.register("eventos", EventoViewSet, basename="eventos")
router.register("inscripciones", InscripcionViewSet, basename="inscripciones")
router.register("resultados", ResultadoViewSet, basename="resultados")
router.register("leyendas", LeyendaViewSet, basename="leyendas")
