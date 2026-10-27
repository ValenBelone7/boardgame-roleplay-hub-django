from django.contrib import admin

from .models import ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ["id", "usuario", "estado", "total", "fecha", "fecha_confirmacion"]
    list_filter = ["estado", "fecha"]
    search_fields = ["usuario__username", "usuario__alias"]
    ordering = ["-fecha"]
    date_hierarchy = "fecha"
    inlines = [ItemPedidoInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ["pedido", "producto", "cantidad", "precio_unitario"]
    list_filter = ["pedido__estado"]
    search_fields = ["producto__nombre", "pedido__usuario__username"]
