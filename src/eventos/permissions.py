from rest_framework import permissions


class EsAutorOSoloLectura(permissions.BasePermission):
    # Cualquiera lee; editar o borrar solo el autor de la leyenda o el staff
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.autor == request.user or request.user.is_staff


class EsInscriptoOSoloLectura(permissions.BasePermission):
    # Cualquiera lee; dar de baja una inscripción solo el inscripto o el staff
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.usuario == request.user or request.user.is_staff
