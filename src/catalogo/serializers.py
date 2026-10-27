from rest_framework import serializers

from usuarios.serializers import UsuarioResumenSerializer

from .models import Categoria, Disenador, Editorial, Mecanica, Producto, Resena


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class EditorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Editorial
        fields = "__all__"


class DisenadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disenador
        fields = "__all__"


class MecanicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mecanica
        fields = "__all__"


class ProductoResumenSerializer(serializers.ModelSerializer):
    # Para anidar desde pedidos y eventos
    class Meta:
        model = Producto
        fields = ["id", "nombre", "tipo", "precio", "imagen_url"]


class ProductoPublicSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    editorial = EditorialSerializer(read_only=True)
    mecanicas = MecanicaSerializer(read_only=True, many=True)
    disenadores = DisenadorSerializer(read_only=True, many=True)
    juego_base = ProductoResumenSerializer(read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Producto
        fields = [
            "id",
            "nombre",
            "descripcion",
            "tipo",
            "tipo_display",
            "precio",
            "stock",
            "jugadores_min",
            "jugadores_max",
            "duracion_minutos",
            "edad_minima",
            "imagen_url",
            "activo",
            "fecha_alta",
            "categoria",
            "editorial",
            "mecanicas",
            "disenadores",
            "juego_base",
        ]


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = [
            "id",
            "nombre",
            "descripcion",
            "tipo",
            "precio",
            "stock",
            "jugadores_min",
            "jugadores_max",
            "duracion_minutos",
            "edad_minima",
            "imagen_url",
            "activo",
            "fecha_alta",
            "categoria",
            "editorial",
            "mecanicas",
            "disenadores",
            "juego_base",
        ]
        read_only_fields = ["id", "fecha_alta"]

    def validate(self, attrs):
        # En un PATCH attrs trae solo lo enviado: lo que falta se toma del producto guardado
        def valor(campo):
            return attrs.get(campo, getattr(self.instance, campo, None))

        jugadores_min = valor("jugadores_min")
        jugadores_max = valor("jugadores_max")
        if jugadores_min and jugadores_max and jugadores_min > jugadores_max:
            raise serializers.ValidationError(
                {"jugadores_max": "Debe ser mayor o igual que jugadores_min."}
            )

        tipo = valor("tipo")
        juego_base = valor("juego_base")
        if tipo == "EXPANSION" and juego_base is None:
            raise serializers.ValidationError(
                {"juego_base": "Una expansión necesita su juego base."}
            )
        if tipo != "EXPANSION" and juego_base is not None:
            raise serializers.ValidationError(
                {"juego_base": "Solo las expansiones tienen juego base."}
            )
        if juego_base is not None and juego_base.tipo == "EXPANSION":
            raise serializers.ValidationError(
                {"juego_base": "El juego base no puede ser una expansión."}
            )
        return attrs


class ResenaPublicSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumenSerializer(read_only=True)
    producto = ProductoResumenSerializer(read_only=True)

    class Meta:
        model = Resena
        fields = ["id", "producto", "usuario", "puntaje", "comentario", "fecha"]


class ResenaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resena
        fields = ["id", "producto", "usuario", "puntaje", "comentario", "fecha"]
        read_only_fields = ["id", "usuario", "fecha"]

    def validate(self, attrs):
        # usuario es read-only, así que DRF no valida el unique_together solo
        request = self.context["request"]
        producto = attrs.get("producto", getattr(self.instance, "producto", None))
        repetidas = Resena.objects.filter(producto=producto, usuario=request.user)
        if self.instance:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError("Ya dejaste una reseña para este producto.")
        return attrs
