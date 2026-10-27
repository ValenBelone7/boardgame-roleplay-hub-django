from rest_framework import serializers

from .models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "alias",
            "first_name",
            "last_name",
            "email",
            "fecha_nacimiento",
            "is_staff",
        ]
        read_only_fields = fields


class UsuarioResumenSerializer(serializers.ModelSerializer):
    # Para anidar en listados públicos sin exponer el email
    class Meta:
        model = Usuario
        fields = ["id", "username", "alias"]


class UsuarioRegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = [
            "username",
            "email",
            "password",
            "alias",
            "first_name",
            "last_name",
            "fecha_nacimiento",
        ]

    def create(self, validated_data):
        # create_user hashea la contraseña; con create() quedaría en texto plano
        return Usuario.objects.create_user(**validated_data)
