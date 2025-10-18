"""DRF permissions for tenant isolation"""
from rest_framework import permissions


class IsTenantMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the request's tenant
    """

    message = "You are not a member of this tenant."

    def has_permission(self, request, view):
        # Allow if no tenant context (main platform endpoints)
        if not hasattr(request, "tenant") or request.tenant is None:
            return True

        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Superadmins have access to all tenants
        if request.user.is_superadmin:
            return True

        # Check if user has membership in this tenant
        return request.user.memberships.filter(
            tenant=request.tenant, is_active=True
        ).exists()


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin of the tenant
    """

    message = "You must be a tenant admin to perform this action."

    def has_permission(self, request, view):
        # Superadmins have access
        if request.user and request.user.is_superadmin:
            return True

        # Check if no tenant context
        if not hasattr(request, "tenant") or request.tenant is None:
            return False

        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is admin in this tenant
        return request.user.memberships.filter(
            tenant=request.tenant, role="SALON_ADMIN", is_active=True
        ).exists()


class IsTenantStaff(permissions.BasePermission):
    """
    Permission for staff members (can view/edit their own data)
    """

    message = "Staff access required."

    def has_permission(self, request, view):
        # Superadmins and salon admins have access
        if request.user and request.user.is_superadmin:
            return True

        if not hasattr(request, "tenant") or request.tenant is None:
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is staff, reception, or admin
        return request.user.memberships.filter(
            tenant=request.tenant,
            role__in=["SALON_ADMIN", "RECEPTION", "STAFF"],
            is_active=True,
        ).exists()


class IsReception(permissions.BasePermission):
    """
    Permission for reception users
    """

    message = "Reception access required."

    def has_permission(self, request, view):
        # Superadmins and salon admins have access
        if request.user and request.user.is_superadmin:
            return True

        if not hasattr(request, "tenant") or request.tenant is None:
            return False

        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user is reception or admin
        return request.user.memberships.filter(
            tenant=request.tenant, role__in=["SALON_ADMIN", "RECEPTION"], is_active=True
        ).exists()


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission for platform superadmins only
    """

    message = "Superadmin access required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superadmin
        )


class TenantObjectPermission(permissions.BasePermission):
    """
    Object-level permission to ensure objects belong to request's tenant
    """

    message = "You don't have permission to access this object."

    def has_object_permission(self, request, view, obj):
        # Superadmins have access to all
        if request.user and request.user.is_superadmin:
            return True

        # Check if object has tenant attribute
        if not hasattr(obj, "tenant"):
            return True

        # Check if request has tenant
        if not hasattr(request, "tenant") or request.tenant is None:
            return False

        # Ensure object belongs to request's tenant
        return obj.tenant_id == request.tenant.id


class ReadOnlyOrAdmin(permissions.BasePermission):
    """
    Read-only for accountants, full access for admins
    """

    message = "You have read-only access."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superadmins have full access
        if request.user.is_superadmin:
            return True

        if not hasattr(request, "tenant") or request.tenant is None:
            return False

        # Admins have full access
        if request.user.memberships.filter(
            tenant=request.tenant, role="SALON_ADMIN", is_active=True
        ).exists():
            return True

        # Accountants have read-only access
        if request.method in permissions.SAFE_METHODS:
            return request.user.memberships.filter(
                tenant=request.tenant, role="ACCOUNTANT", is_active=True
            ).exists()

        return False
