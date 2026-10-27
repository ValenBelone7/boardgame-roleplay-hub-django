from rest_framework import serializers

from catalogo.serializers import ProductoResumenSerializer
from usuarios.serializers import UsuarioResumenSerializer

from .models import Evento, Inscripcion, Leyenda, Resultado


class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = "__all__"


class EventoResumenSerializer(serializers.ModelSerializer):
    # Para anidar en resultados y leyendas
    class Meta:
        model = Evento
        fields = ["id", "nombre", "tipo", "fecha"]


class EventoPublicSerializer(serializers.ModelSerializer):
    juego = ProductoResumenSerializer(read_only=True)
    organizador = UsuarioResumenSerializer(read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    inscriptos = serializers.IntegerField(source="inscripciones.count", read_only=True)

    class Meta:
        model = Evento
        fields = [
            "id",
            "nombre",
            "descripcion",
            "tipo",
            "tipo_display",
            "juego",
            "organizador",
            "fecha",
            "cupo",
            "inscriptos",
            "costo_inscripcion",
            "estado",
            "estado_display",
        ]


class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inscripcion
        fields = ["id", "evento", "usuario", "personaje", "fecha"]
        read_only_fields = ["id", "usuario", "fecha"]

    def validate(self, attrs):
        # usuario es read-only, así que DRF no valida el unique_together solo
        request = self.context["request"]
        evento = attrs.get("evento", getattr(self.instance, "evento", None))
        repetidas = Inscripcion.objects.filter(evento=evento, usuario=request.user)
        if self.instance:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError("Ya estás inscripto en este evento.")
        return attrs


class ResultadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resultado
        fields = "__all__"


class ResultadoPublicSerializer(serializers.ModelSerializer):
    evento = EventoResumenSerializer(read_only=True)
    usuario = UsuarioResumenSerializer(read_only=True)

    class Meta:
        model = Resultado
        fields = ["id", "evento", "posicion", "usuario", "puntos"]


class LeyendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leyenda
        fields = ["id", "evento", "autor", "protagonista", "titulo", "relato", "destacada", "fecha"]
        # destacada la marca el staff desde el admin
        read_only_fields = ["id", "autor", "destacada", "fecha"]


class LeyendaPublicSerializer(serializers.ModelSerializer):
    evento = EventoResumenSerializer(read_only=True)
    autor = UsuarioResumenSerializer(read_only=True)
    protagonista = UsuarioResumenSerializer(read_only=True)

    class Meta:
        model = Leyenda
        fields = ["id", "evento", "autor", "protagonista", "titulo", "relato", "destacada", "fecha"]
