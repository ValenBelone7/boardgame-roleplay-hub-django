from django.conf import settings
from django.db import models

from catalogo.models import Producto


class Pedido(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("CONFIRMADO", "Confirmado"),
        ("CANCELADO", "Cancelado"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedidos"
    )
    estado = models.CharField(max_length=10, choices=ESTADOS, default="PENDIENTE")
    # Se calcula al confirmar el pedido
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Pedido #{self.id} de {self.usuario}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="items_pedido")
    cantidad = models.PositiveIntegerField(default=1)
    # Precio congelado al momento de agregarlo, aunque después cambie en el catálogo
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]
        verbose_name = "ítem de pedido"
        verbose_name_plural = "ítems de pedido"

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
