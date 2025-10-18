from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"locations", views.LocationViewSet, basename="location")
router.register(
    r"service-categories", views.ServiceCategoryViewSet, basename="service-category"
)
router.register(r"services", views.ServiceViewSet, basename="service")
router.register(r"staff", views.StaffViewSet, basename="staff")
router.register(r"schedules", views.ScheduleViewSet, basename="schedule")
router.register(r"customers", views.CustomerViewSet, basename="customer")
router.register(r"appointments", views.AppointmentViewSet, basename="appointment")

urlpatterns = [
    # Public endpoints (for widget)
    path("available-slots/", views.available_slots, name="available_slots"),
    path("create-appointment/", views.create_appointment, name="create_appointment"),
    # Include router URLs
    path("", include(router.urls)),
]
