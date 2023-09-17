from rest_framework import permissions


class AuthorPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        authenticated = request.user.is_authenticated
        safe_method = request.method in permissions.SAFE_METHODS
        return authenticated and safe_method

    def has_object_permission(self, request, view, obj):
        return request.user == obj.author
