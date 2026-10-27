from django.db.models import Count, Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from nucleo.permissions import EsStaffOSoloLectura
from usuarios.models import Usuario

from .models import Evento, Inscripcion, Leyenda, Resultado
from .permissions import EsAutorOSoloLectura, EsInscriptoOSoloLectura
from .serializers import (
    EventoPublicSerializer,
    EventoSerializer,
    InscripcionSerializer,
    LeyendaPublicSerializer,
    LeyendaSerializer,
    ResultadoPublicSerializer,
    ResultadoSerializer,
    SalonDeLaFamaSerializer,
)


class EventoViewSet(viewsets.ModelViewSet):
    """Eventos de Arcana: torneos, partidas y campañas de rol, noches de juegos.
    Todos los ven; solo el staff los organiza. Los usuarios se anotan con inscribirse."""

    queryset = Evento.objects.select_related("juego", "organizador").prefetch_related(
        "inscripciones"
    )
    permission_classes = [EsStaffOSoloLectura]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "tipo": ["exact"],
        "estado": ["exact"],
        "juego": ["exact"],
        "fecha": ["gte", "lte"],
    }
    search_fields = ["nombre", "juego__nombre"]
    ordering_fields = ["fecha", "costo_inscripcion"]

    def get_serializer_class(self):
        if self.action == "list":
            return EventoPublicSerializer
        return EventoSerializer

    @extend_schema(
        summary="Inscribirse a un evento",
        description="Anota al usuario logueado. El personaje es opcional (partidas de rol).",
        request=inline_serializer(
            name="InscribirseRequest",
            fields={"personaje": serializers.CharField(required=False)},
        ),
        responses={
            201: InscripcionSerializer,
            400: OpenApiResponse(description="Evento cerrado, sin cupo o ya inscripto"),
            401: OpenApiResponse(description="No autenticado"),
        },
    )
    # Sin esto hereda EsStaffOSoloLectura y un usuario común no podría inscribirse
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def inscribirse(self, request, pk=None):
        evento = self.get_object()
        if evento.estado != "PROGRAMADO":
            return Response(
                {"error": "Las inscripciones de este evento están cerradas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if evento.inscripciones.filter(usuario=request.user).exists():
            return Response(
                {"error": "Ya estás inscripto en este evento."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if evento.inscripciones.count() >= evento.cupo:
            return Response(
                {"error": "El evento no tiene más cupo."}, status=status.HTTP_400_BAD_REQUEST
            )
        inscripcion = Inscripcion.objects.create(
            evento=evento, usuario=request.user, personaje=request.data.get("personaje", "")
        )
        return Response(InscripcionSerializer(inscripcion).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Podio del evento",
        description="Resultados del evento ordenados por posición (1 = campeón).",
        responses={200: ResultadoPublicSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def podio(self, request, pk=None):
        evento = self.get_object()
        resultados = evento.resultados.select_related("evento", "usuario").order_by("posicion")
        return Response(ResultadoPublicSerializer(resultados, many=True).data)


class InscripcionViewSet(viewsets.ModelViewSet):
    """Inscripciones a eventos. Para anotarse se usa eventos/{id}/inscribirse/.
    Cada uno puede darse de baja de la suya mientras el evento no haya empezado."""

    queryset = Inscripcion.objects.select_related("evento", "usuario")
    serializer_class = InscripcionSerializer
    permission_classes = [IsAuthenticated, EsInscriptoOSoloLectura]
    # Sin POST: así nadie se saltea las reglas de cupo y estado de inscribirse
    http_method_names = ["get", "delete", "head", "options"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["evento", "usuario"]

    def perform_destroy(self, instance):
        if instance.evento.estado != "PROGRAMADO":
            raise ValidationError({"error": "El evento ya empezó o terminó."})
        instance.delete()


class ResultadoViewSet(viewsets.ModelViewSet):
    """Tabla de ganadores: una fila por puesto en el podio de cada evento.
    Todos la ven; solo el staff carga resultados."""

    queryset = Resultado.objects.select_related("evento", "usuario")
    permission_classes = [EsStaffOSoloLectura]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["evento", "usuario", "posicion"]
    ordering_fields = ["posicion", "puntos"]

    def get_serializer_class(self):
        if self.action == "list":
            return ResultadoPublicSerializer
        return ResultadoSerializer

    @extend_schema(
        summary="Salón de la fama",
        description="Ranking de jugadores por títulos (primeros puestos) y después por puntos.",
        responses={200: SalonDeLaFamaSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def salon_de_la_fama(self, request):
        ranking = (
            Usuario.objects.annotate(
                titulos=Count("resultados", filter=Q(resultados__posicion=1)),
                podios=Count("resultados"),
                puntos=Sum("resultados__puntos"),
            )
            .filter(podios__gt=0)
            .order_by("-titulos", "-puntos", "username")
        )
        pagina = self.paginate_queryset(ranking)
        serializer = SalonDeLaFamaSerializer(pagina, many=True)
        return self.get_paginated_response(serializer.data)


class LeyendaViewSet(viewsets.ModelViewSet):
    """Leyendas: crónicas de lo que pasó en la mesa. Cualquiera las lee; los usuarios
    logueados escriben las suyas y el staff destaca las mejores desde el admin."""

    queryset = Leyenda.objects.select_related("evento", "autor", "protagonista")
    permission_classes = [IsAuthenticatedOrReadOnly, EsAutorOSoloLectura]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["evento", "destacada", "autor", "protagonista"]
    search_fields = ["titulo", "relato"]
    ordering_fields = ["fecha"]

    def get_serializer_class(self):
        if self.action == "list":
            return LeyendaPublicSerializer
        return LeyendaSerializer

    @extend_schema(
        summary="Escribir una leyenda",
        description="El autor es el usuario logueado. Solo el staff puede destacarla.",
        responses={
            201: LeyendaSerializer,
            400: OpenApiResponse(description="Datos inválidos"),
            401: OpenApiResponse(description="No autenticado"),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # El autor es siempre el usuario logueado, no viene en el body
        serializer.save(autor=self.request.user)
