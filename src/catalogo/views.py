from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from nucleo.permissions import EsStaffOSoloLectura

from .models import Categoria, Disenador, Editorial, Mecanica, Producto, Resena
from .permissions import EsAutorOSoloLectura
from .serializers import (
    CategoriaSerializer,
    DisenadorSerializer,
    EditorialSerializer,
    MecanicaSerializer,
    ProductoPublicSerializer,
    ProductoSerializer,
    ResenaPublicSerializer,
    ResenaSerializer,
)


class CategoriaViewSet(viewsets.ModelViewSet):
    """Categorías del catálogo (Estrategia, Party, Rol...). Todos leen, solo el staff edita."""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [EsStaffOSoloLectura]
    filter_backends = [SearchFilter]
    search_fields = ["nombre"]

    def destroy(self, request, *args, **kwargs):
        # categoria es PROTECT en Producto: sin esto, borrar una con productos da 500
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "La categoría tiene productos asociados."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EditorialViewSet(viewsets.ModelViewSet):
    """Editoriales de los juegos. Todos leen, solo el staff edita."""

    queryset = Editorial.objects.all()
    serializer_class = EditorialSerializer
    permission_classes = [EsStaffOSoloLectura]
    filter_backends = [SearchFilter]
    search_fields = ["nombre"]


class DisenadorViewSet(viewsets.ModelViewSet):
    """Diseñadores de los juegos. Todos leen, solo el staff edita."""

    queryset = Disenador.objects.all()
    serializer_class = DisenadorSerializer
    permission_classes = [EsStaffOSoloLectura]
    filter_backends = [SearchFilter]
    search_fields = ["nombre"]


class MecanicaViewSet(viewsets.ModelViewSet):
    """Mecánicas de juego (Draft, Deckbuilding, Narrativa...). Todos leen, solo el staff edita."""

    queryset = Mecanica.objects.all()
    serializer_class = MecanicaSerializer
    permission_classes = [EsStaffOSoloLectura]
    filter_backends = [SearchFilter]
    search_fields = ["nombre"]


class ProductoViewSet(viewsets.ModelViewSet):
    """Catálogo de Arcana: juegos de mesa, de rol, expansiones y accesorios.
    Todos pueden consultarlo; solo el staff da de alta, edita o borra."""

    queryset = Producto.objects.select_related(
        "categoria", "editorial", "juego_base"
    ).prefetch_related("mecanicas", "disenadores")
    permission_classes = [EsStaffOSoloLectura]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "categoria": ["exact"],
        "editorial": ["exact"],
        "tipo": ["exact"],
        "activo": ["exact"],
        "mecanicas": ["exact"],
        "precio": ["exact", "gt", "lt", "gte", "lte"],
        "jugadores_min": ["lte"],
        "jugadores_max": ["gte"],
    }
    search_fields = ["nombre", "editorial__nombre", "disenadores__nombre", "mecanicas__nombre"]
    ordering_fields = ["precio", "nombre", "fecha_alta"]

    def get_serializer_class(self):
        # La consigna pide anidados solo en el listado
        if self.action == "list":
            return ProductoPublicSerializer
        return ProductoSerializer

    @extend_schema(
        summary="Dar de alta un producto",
        description="Solo staff. Las relaciones (categoría, editorial, mecánicas...) van por id.",
        responses={
            201: ProductoSerializer,
            400: OpenApiResponse(description="Datos inválidos (ej. expansión sin juego base)"),
            401: OpenApiResponse(description="No autenticado"),
            403: OpenApiResponse(description="Solo el staff puede crear productos"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Un producto ya vendido no se puede borrar (ItemPedido.producto es PROTECT)
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "El producto tiene pedidos. Usá borrado_logico para darlo de baja."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Dar de baja un producto (borrado lógico)",
        description="Solo staff. Marca el producto como inactivo sin borrarlo de la base.",
        request=None,
        responses={
            200: OpenApiResponse(description="Producto dado de baja"),
            403: OpenApiResponse(description="Solo el staff puede dar de baja productos"),
            404: OpenApiResponse(description="El producto no existe"),
        },
    )
    @action(detail=True, methods=["delete"])
    def borrado_logico(self, request, pk=None):
        producto = self.get_object()
        producto.activo = False
        producto.save()
        return Response({"status": "Producto dado de baja con éxito"})

    @extend_schema(
        summary="Reseñas de un producto",
        description="Reseñas del producto, paginadas y de la más nueva a la más vieja.",
        responses={200: ResenaPublicSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def resenas(self, request, pk=None):
        producto = self.get_object()
        resenas = producto.resenas.select_related("usuario", "producto")
        # Paginado igual que un list normal
        pagina = self.paginate_queryset(resenas)
        serializer = ResenaPublicSerializer(pagina, many=True)
        return self.get_paginated_response(serializer.data)


class ResenaViewSet(viewsets.ModelViewSet):
    """Reseñas de los productos. Cualquiera las lee; para escribir hay que estar logueado,
    y solo el autor (o el staff) puede editar o borrar la suya."""

    queryset = Resena.objects.select_related("usuario", "producto")
    permission_classes = [IsAuthenticatedOrReadOnly, EsAutorOSoloLectura]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["producto", "usuario", "puntaje"]
    ordering_fields = ["fecha", "puntaje"]

    def get_serializer_class(self):
        if self.action == "list":
            return ResenaPublicSerializer
        return ResenaSerializer

    @extend_schema(
        summary="Escribir una reseña",
        description="El autor es el usuario logueado. Una sola reseña por producto.",
        responses={
            201: ResenaSerializer,
            400: OpenApiResponse(description="Reseña duplicada o puntaje fuera de 1 a 5"),
            401: OpenApiResponse(description="No autenticado"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # El autor es siempre el usuario logueado, no viene en el body
        serializer.save(usuario=self.request.user)
