from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ItemPedido, Pedido
from .serializers import (
    ItemPedidoPublicSerializer,
    ItemPedidoSerializer,
    PedidoPublicSerializer,
    PedidoSerializer,
)


class PedidoViewSet(viewsets.ModelViewSet):
    """Pedidos de la tienda. Cada usuario ve y maneja solo los suyos; el staff ve todos.
    El pedido se crea vacío, se le agregan ítems y se confirma o cancela con sus actions."""

    queryset = Pedido.objects.select_related("usuario").prefetch_related("items__producto")
    permission_classes = [IsAuthenticated]
    # Sin PUT/PATCH/DELETE: el estado cambia solo con confirmar y cancelar
    http_method_names = ["get", "post", "head", "options"]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado"]
    ordering_fields = ["fecha", "total"]

    def get_queryset(self):
        # Al generar el schema de Swagger no hay usuario real
        if getattr(self, "swagger_fake_view", False):
            return Pedido.objects.none()
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(usuario=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return PedidoPublicSerializer
        return PedidoSerializer

    @extend_schema(
        summary="Crear un pedido",
        description="Crea un pedido vacío para el usuario logueado (no lleva body).",
        request=None,
        responses={
            201: PedidoSerializer,
            400: OpenApiResponse(description="Ya tiene un pedido pendiente"),
            401: OpenApiResponse(description="No autenticado"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Un solo pedido pendiente por usuario: funciona como carrito
        if Pedido.objects.filter(usuario=self.request.user, estado="PENDIENTE").exists():
            raise ValidationError({"error": "Ya tenés un pedido pendiente."})
        serializer.save(usuario=self.request.user)

    @extend_schema(
        summary="Confirmar un pedido",
        description="Controla el stock, lo descuenta y calcula el total del pedido.",
        request=None,
        responses={
            200: PedidoSerializer,
            400: OpenApiResponse(description="No está pendiente, está vacío o falta stock"),
            404: OpenApiResponse(description="El pedido no existe o no es tuyo"),
        },
    )
    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        pedido = self.get_object()
        if pedido.estado != "PENDIENTE":
            return Response(
                {"error": "Solo se puede confirmar un pedido pendiente."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        items = pedido.items.select_related("producto")
        if not items:
            return Response(
                {"error": "El pedido no tiene ítems."}, status=status.HTTP_400_BAD_REQUEST
            )
        # Primero se revisa todo; si algo falla no se descuenta nada
        for item in items:
            if not item.producto.activo:
                return Response(
                    {"error": f"{item.producto.nombre} ya no está a la venta."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if item.cantidad > item.producto.stock:
                return Response(
                    {
                        "error": f"No hay stock suficiente de {item.producto.nombre} "
                        f"(quedan {item.producto.stock})."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        with transaction.atomic():
            for item in items:
                item.producto.stock -= item.cantidad
                item.producto.save()
            pedido.total = sum(item.cantidad * item.precio_unitario for item in items)
            pedido.estado = "CONFIRMADO"
            pedido.fecha_confirmacion = timezone.now()
            pedido.save()
        return Response(PedidoSerializer(pedido).data)

    @extend_schema(
        summary="Cancelar un pedido",
        description="Si el pedido estaba confirmado, repone el stock.",
        request=None,
        responses={
            200: PedidoSerializer,
            400: OpenApiResponse(description="El pedido ya está cancelado"),
            404: OpenApiResponse(description="El pedido no existe o no es tuyo"),
        },
    )
    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        pedido = self.get_object()
        if pedido.estado == "CANCELADO":
            return Response(
                {"error": "El pedido ya está cancelado."}, status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            # Si ya se había descontado el stock, se repone
            if pedido.estado == "CONFIRMADO":
                for item in pedido.items.select_related("producto"):
                    item.producto.stock += item.cantidad
                    item.producto.save()
            pedido.estado = "CANCELADO"
            pedido.save()
        return Response(PedidoSerializer(pedido).data)


class ItemPedidoViewSet(viewsets.ModelViewSet):
    """Ítems de los pedidos. Solo se pueden agregar, cambiar o quitar mientras el pedido
    propio está pendiente. El precio se toma del catálogo al agregarlo."""

    queryset = ItemPedido.objects.select_related("pedido", "producto")
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["pedido"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ItemPedido.objects.none()
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(pedido__usuario=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ItemPedidoPublicSerializer
        return ItemPedidoSerializer

    def validar(self, pedido, producto, item=None):
        if pedido.usuario != self.request.user:
            raise ValidationError({"pedido": "El pedido no es tuyo."})
        if pedido.estado != "PENDIENTE":
            raise ValidationError({"pedido": "El pedido ya no se puede modificar."})
        if not producto.activo:
            raise ValidationError({"producto": "El producto ya no está a la venta."})
        repetidos = pedido.items.filter(producto=producto)
        if item:
            repetidos = repetidos.exclude(pk=item.pk)
        if repetidos.exists():
            raise ValidationError({"producto": "Ya está en el pedido, editá la cantidad."})

    @extend_schema(
        summary="Agregar un producto al pedido",
        description="El precio unitario se copia del catálogo en este momento.",
        responses={
            201: ItemPedidoSerializer,
            400: OpenApiResponse(
                description="Pedido ajeno o no pendiente, producto inactivo o repetido"
            ),
            401: OpenApiResponse(description="No autenticado"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        producto = serializer.validated_data["producto"]
        self.validar(serializer.validated_data["pedido"], producto)
        # Precio congelado al momento de agregarlo
        serializer.save(precio_unitario=producto.precio)

    def perform_update(self, serializer):
        item = serializer.instance
        # Se revisa el pedido original y también el nuevo, por si lo cambian
        if item.pedido.estado != "PENDIENTE":
            raise ValidationError({"pedido": "El pedido ya no se puede modificar."})
        producto = serializer.validated_data.get("producto", item.producto)
        self.validar(serializer.validated_data.get("pedido", item.pedido), producto, item)
        serializer.save(precio_unitario=producto.precio)

    def perform_destroy(self, instance):
        if instance.pedido.estado != "PENDIENTE":
            raise ValidationError({"pedido": "El pedido ya no se puede modificar."})
        instance.delete()
