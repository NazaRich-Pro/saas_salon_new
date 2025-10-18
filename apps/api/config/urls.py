"""
URL configuration for BeautyHub SaaS project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Public registration endpoints (no /api prefix for easier access)
    path("api/register-salon/", include("apps.tenants.urls")),
    path("api/register-solo/", include("apps.tenants.urls")),
    # API endpoints
    path("api/health/", include("apps.users.urls")),  # Health check
    path("api/auth/", include("apps.users.urls")),
    path("api/tenants/", include("apps.tenants.urls")),
    path("api/booking/", include("apps.booking.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
