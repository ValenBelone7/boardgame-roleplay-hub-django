from rest_framework import serializers

from catalogo.serializers import ProductoResumenSerializer
from usuarios.serializers import UsuarioResumenSerializer

from .models import ItemPedido, Pedido


class ItemPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedido
        fields = ["id", "pedido", "producto", "cantidad", "precio_unitario"]
        # El precio se copia del producto al agregarlo (perform_create)
        read_only_fields = ["id", "precio_unitario"]

    def validate_cantidad(self, value):
        if value < 1:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value


class ItemPedidoPublicSerializer(serializers.ModelSerializer):
    producto = ProductoResumenSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = ItemPedido
        fields = ["id", "producto", "cantidad", "precio_unitario", "subtotal"]

    def get_subtotal(self, obj) -> str:
        # Como texto, igual que precio_unitario y total ("80000.00")
        return str(obj.cantidad * obj.precio_unitario)


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = ["id", "usuario", "estado", "total", "fecha", "fecha_confirmacion"]
        # El pedido se crea vacío y cambia de estado solo con confirmar / cancelar
        read_only_fields = fields


class PedidoPublicSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumenSerializer(read_only=True)
    items = ItemPedidoPublicSerializer(read_only=True, many=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Pedido
        fields = [
            "id",
            "usuario",
            "estado",
            "estado_display",
            "total",
            "fecha",
            "fecha_confirmacion",
            "items",
        ]
