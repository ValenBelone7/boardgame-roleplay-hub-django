from rest_framework import permissions


class EsStaffOSoloLectura(permissions.BasePermission):
    # Cualquiera puede leer (GET, HEAD, OPTIONS), solo el staff puede crear, editar o borrar
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff
