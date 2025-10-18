"""
Custom permissions for user roles and access control.
"""
from rest_framework import permissions


class IsAccountant(permissions.BasePermission):
    """
    Permission check for Accountant role (read-only access to financial data).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has ACCOUNTANT role for current tenant
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        from apps.tenants.models import Membership

        try:
            membership = Membership.objects.get(user=request.user, tenant=tenant)
            return membership.role == Membership.ROLE_ACCOUNTANT
        except Membership.DoesNotExist:
            return False


class IsAccountantOrAdmin(permissions.BasePermission):
    """
    Permission check for Accountant or Admin roles.
    Accountants have read-only access, Admins have full access.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        from apps.tenants.models import Membership

        try:
            membership = Membership.objects.get(user=request.user, tenant=tenant)

            # Allow if Admin or Salon Admin
            if membership.role in [Membership.ROLE_SALON_ADMIN]:
                return True

            # Accountants only for safe methods (GET, HEAD, OPTIONS)
            if membership.role == Membership.ROLE_ACCOUNTANT:
                return request.method in permissions.SAFE_METHODS

            return False
        except Membership.DoesNotExist:
            return False
