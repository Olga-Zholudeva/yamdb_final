from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_admin
                or request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        return (request.user.is_admin
                or request.user.is_staff)


class IsAuthorOrModeratorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (obj.author == request.user
                    or request.user.role == "admin"
                    or request.user.role == "moderator"))


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (not request.user.is_anonymous
                    and request.user.role == "admin"))

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (not request.user.is_anonymous
                    and request.user.role == "admin"))
