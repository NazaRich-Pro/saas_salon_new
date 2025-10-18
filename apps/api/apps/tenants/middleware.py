"""Tenant resolution middleware"""
import logging

from django.conf import settings
from django.core.cache import cache

from .models import Tenant, TenantDomain

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware to resolve tenant from request host
    Sets request.tenant based on subdomain or custom domain
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        primary_domain = settings.PRIMARY_DOMAIN.lower()

        request.tenant = None
        request.tenant_slug = None

        # Try to get tenant from cache first
        cache_key = f"tenant_by_host:{host}"
        tenant_id = cache.get(cache_key)

        if tenant_id:
            try:
                request.tenant = Tenant.objects.get(
                    id=tenant_id, status__in=["TRIAL", "ACTIVE", "GRACE"]
                )
                request.tenant_slug = request.tenant.slug
            except Tenant.DoesNotExist:
                # Cache was stale, continue with resolution
                cache.delete(cache_key)
                tenant_id = None

        if not tenant_id:
            tenant = self._resolve_tenant(host, primary_domain)

            if tenant:
                request.tenant = tenant
                request.tenant_slug = tenant.slug
                # Cache for 5 minutes
                cache.set(cache_key, str(tenant.id), 300)
            else:
                # No tenant found, set to None (main platform)
                request.tenant = None
                request.tenant_slug = None

        # Log resolution for debugging
        if request.tenant:
            logger.debug(
                f"Resolved tenant: {request.tenant.name} (slug: {request.tenant.slug}) from host: {host}"
            )
        else:
            logger.debug(f"No tenant resolved for host: {host} (main platform)")

        response = self.get_response(request)

        # Add tenant info to response headers for debugging
        if request.tenant:
            response["X-Tenant-Slug"] = request.tenant.slug
            response["X-Tenant-ID"] = str(request.tenant.id)

        return response

    def _resolve_tenant(self, host, primary_domain):
        """
        Resolve tenant from host
        Returns Tenant object or None
        """
        try:
            # Case 1: Subdomain of primary domain (e.g., demo.saas.akylman.online)
            if host.endswith(f".{primary_domain}"):
                subdomain = host.replace(f".{primary_domain}", "")

                # Validate subdomain format (alphanumeric and hyphens only)
                if subdomain and subdomain.replace("-", "").isalnum():
                    tenant = Tenant.objects.filter(
                        slug=subdomain, status__in=["TRIAL", "ACTIVE", "GRACE"]
                    ).first()

                    if tenant:
                        return tenant
                    else:
                        logger.warning(f"No tenant found for subdomain: {subdomain}")
                        return None

            # Case 2: Main domain (e.g., saas.akylman.online)
            elif host == primary_domain:
                # This is the main platform, no tenant
                return None

            # Case 3: Custom domain (white-label)
            else:
                # Look up in TenantDomain table
                tenant_domain = (
                    TenantDomain.objects.select_related("tenant")
                    .filter(
                        domain=host,
                        verified_at__isnull=False,
                        tenant__status__in=["TRIAL", "ACTIVE", "GRACE"],
                    )
                    .first()
                )

                if tenant_domain:
                    logger.info(
                        f"Resolved custom domain: {host} → {tenant_domain.tenant.name}"
                    )
                    return tenant_domain.tenant
                else:
                    logger.warning(f"No tenant found for custom domain: {host}")
                    return None

        except Exception as e:
            logger.error(f"Error resolving tenant for host {host}: {str(e)}")
            return None
