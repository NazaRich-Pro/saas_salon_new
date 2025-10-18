from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, views_reports

router = DefaultRouter()
router.register(r"appointments", views.AppointmentViewSet, basename="appointment")

urlpatterns = [
    path("", include(router.urls)),
    path("available-slots/", views.available_slots, name="available_slots"),
    # Reports
    path("reports/revenue/", views_reports.revenue_report, name="revenue_report"),
    path("reports/no-show/", views_reports.no_show_report, name="no_show_report"),
    path("reports/kpi/", views_reports.kpi_report, name="kpi_report"),
    path(
        "reports/export.csv", views_reports.export_csv, name="export_appointments_csv"
    ),
    path(
        "reports/payments-export.csv",
        views_reports.payments_export_csv,
        name="export_payments_csv",
    ),
]
