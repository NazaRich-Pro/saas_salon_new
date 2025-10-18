"""Mixins for tenant-scoped views and querysets"""
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response


class TenantQuerysetMixin:
    """
    Mixin to automatically filter querysets by tenant
    """

    tenant_field = "tenant"

    def get_queryset(self):
        """
        Filter queryset by request's tenant
        """
        queryset = super().get_queryset()

        # If no tenant in request, return empty queryset (except for superadmins)
        if not hasattr(self.request, "tenant") or self.request.tenant is None:
            if self.request.user and self.request.user.is_superadmin:
                return queryset
            return queryset.none()

        # Filter by tenant
        filter_kwargs = {self.tenant_field: self.request.tenant}
        return queryset.filter(**filter_kwargs)


class TenantCreateMixin:
    """
    Mixin to automatically set tenant on object creation
    """

    def perform_create(self, serializer):
        """
        Set tenant when creating object
        """
        if not hasattr(self.request, "tenant") or self.request.tenant is None:
            raise PermissionDenied("No tenant context available")

        serializer.save(tenant=self.request.tenant)


class TenantUpdateMixin:
    """
    Mixin to prevent changing tenant on updates
    """

    def perform_update(self, serializer):
        """
        Ensure tenant is not changed on update
        """
        # Remove tenant from validated_data if present
        if "tenant" in serializer.validated_data:
            serializer.validated_data.pop("tenant")

        serializer.save()


class TenantRequiredMixin:
    """
    Mixin to require tenant in request
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # Skip check for superadmins
        if request.user and request.user.is_superadmin:
            return

        # Ensure tenant is present
        if not hasattr(request, "tenant") or request.tenant is None:
            return Response(
                {
                    "detail": "Tenant context required. Please access via tenant subdomain."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class AuditLogMixin:
    """
    Mixin to automatically create audit logs for actions
    """

    def perform_create(self, serializer):
        instance = serializer.save()
        self._create_audit_log("CREATE", instance)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        self._create_audit_log("UPDATE", instance)
        return instance

    def perform_destroy(self, instance):
        self._create_audit_log("DELETE", instance)
        instance.delete()

    def _create_audit_log(self, action, instance):
        """Create audit log entry"""
        from apps.payments.models import AuditLog

        # Get IP address
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0]
        else:
            ip_address = self.request.META.get("REMOTE_ADDR")

        # Get user agent
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")

        # Get tenant
        tenant = getattr(self.request, "tenant", None)

        # Create log
        AuditLog.objects.create(
            tenant=tenant,
            user=self.request.user if self.request.user.is_authenticated else None,
            action=action,
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            metadata={
                "changes": getattr(self, "serializer", {}).get("validated_data", {})
                if hasattr(self, "serializer")
                else {}
            },
            ip_address=ip_address,
            user_agent=user_agent[:500],  # Limit length
        )


class TenantViewSetMixin(TenantQuerysetMixin, TenantCreateMixin, TenantUpdateMixin):
    """
    Combined mixin for tenant-scoped viewsets
    Includes queryset filtering, automatic tenant setting, and update protection
    """

    pass
