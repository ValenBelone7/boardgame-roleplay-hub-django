from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Usuario
from .serializers import (
    UsuarioRegistroSerializer,
    UsuarioResumenSerializer,
    UsuarioSerializer,
)


class UsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """Usuarios de Arcana. Registro abierto; para ver usuarios hay que estar logueado.
    Solo el staff ve los datos completos (email, nombre, fecha de nacimiento)."""

    queryset = Usuario.objects.all().order_by("id")
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ["username", "alias"]

    def get_serializer_class(self):
        if self.action == "registro":
            return UsuarioRegistroSerializer
        if self.action == "me" or self.request.user.is_staff:
            return UsuarioSerializer
        # El resto ve solo id, username y alias (sin email)
        return UsuarioResumenSerializer

    @extend_schema(
        summary="Registrar usuario",
        description="Crea una cuenta nueva. Después se obtiene el token en /api/token/.",
        request=UsuarioRegistroSerializer,
        responses={
            201: UsuarioSerializer,
            400: OpenApiResponse(description="Datos inválidos o usuario ya existente"),
        },
    )
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def registro(self, request):
        serializer = UsuarioRegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Mis datos",
        description="Datos del usuario logueado.",
        responses={
            200: UsuarioSerializer,
            401: OpenApiResponse(description="No autenticado"),
        },
    )
    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UsuarioSerializer(request.user).data)
