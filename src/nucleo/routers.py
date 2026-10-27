from rest_framework.routers import DefaultRouter

from catalogo.views import (
    CategoriaViewSet,
    DisenadorViewSet,
    EditorialViewSet,
    MecanicaViewSet,
    ProductoViewSet,
    ResenaViewSet,
)
from usuarios.views import UsuarioViewSet

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuarios")
router.register("categorias", CategoriaViewSet, basename="categorias")
router.register("editoriales", EditorialViewSet, basename="editoriales")
router.register("disenadores", DisenadorViewSet, basename="disenadores")
router.register("mecanicas", MecanicaViewSet, basename="mecanicas")
router.register("productos", ProductoViewSet, basename="productos")
router.register("resenas", ResenaViewSet, basename="resenas")
