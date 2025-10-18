"""Booking views and viewsets"""
from apps.tenants.mixins import TenantRequiredMixin, TenantViewSetMixin
from apps.tenants.permissions import IsReception, IsTenantAdmin, IsTenantMember
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .ics_export import generate_ics, generate_ics_filename
from .models import (
    Appointment,
    Customer,
    Location,
    Schedule,
    Service,
    ServiceCategory,
    Staff,
    StaffService,
)
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentRescheduleSerializer,
    AppointmentSerializer,
    AppointmentStatusSerializer,
    AvailableSlotsSerializer,
    CustomerSerializer,
    LocationSerializer,
    ScheduleSerializer,
    ServiceCategorySerializer,
    ServiceSerializer,
    SlotSerializer,
    StaffSerializer,
    StaffServiceSerializer,
)
from .services import AppointmentCreationError
from .services import AppointmentService as AppointmentBusinessService
from .slot_engine import SlotGenerator


class LocationViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for locations"""

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class ServiceCategoryViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for service categories"""

    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            return qs.filter(is_active=True).order_by("sort_order", "name")
        return qs


class ServiceViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for services"""

    queryset = Service.objects.select_related("category").all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        qs = super().get_queryset()

        if self.action == "list":
            qs = qs.filter(is_active=True)

            # Filter by category
            category_id = self.request.query_params.get("category")
            if category_id:
                qs = qs.filter(category_id=category_id)

        return qs.order_by("category__sort_order", "name")


class StaffViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for staff members"""

    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "list":
            qs = qs.filter(is_active=True)
        return qs


class ScheduleViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for staff schedules"""

    queryset = Schedule.objects.select_related("staff").all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]


class CustomerViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for customers"""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsReception]

    def get_queryset(self):
        qs = super().get_queryset()

        # Search by phone or name
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(phone__icontains=search)
                | Q(name__icontains=search)
                | Q(email__icontains=search)
            )

        return qs.order_by("-created_at")


class AppointmentViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for appointments"""

    queryset = (
        Appointment.objects.select_related("customer", "staff", "location")
        .prefetch_related("services__service")
        .all()
    )
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsReception]

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by staff
        staff_id = self.request.query_params.get("staff")
        if staff_id:
            qs = qs.filter(staff_id=staff_id)

        # Filter by date range
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if date_from:
            qs = qs.filter(start_at__gte=date_from)
        if date_to:
            qs = qs.filter(start_at__lte=date_to)

        return qs.order_by("-start_at")

    @action(detail=True, methods=["patch"], url_path="confirm")
    def confirm(self, request, pk=None):
        """Confirm a pending appointment"""
        appointment_service = AppointmentBusinessService(request.tenant)

        try:
            appointment = appointment_service.confirm_appointment(pk)
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        except AppointmentCreationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        status_serializer = AppointmentStatusSerializer(data=request.data)
        status_serializer.is_valid(raise_exception=True)

        reason = status_serializer.validated_data.get("reason", "")

        appointment_service = AppointmentBusinessService(request.tenant)

        try:
            appointment = appointment_service.cancel_appointment(pk, reason)
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        except AppointmentCreationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="reschedule")
    def reschedule(self, request, pk=None):
        """Reschedule an appointment"""
        reschedule_serializer = AppointmentRescheduleSerializer(data=request.data)
        reschedule_serializer.is_valid(raise_exception=True)

        new_start_at = reschedule_serializer.validated_data["new_start_at"]
        new_staff_id = reschedule_serializer.validated_data.get("new_staff_id")

        appointment_service = AppointmentBusinessService(request.tenant)

        try:
            appointment = appointment_service.reschedule_appointment(
                pk, new_start_at, new_staff_id
            )
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        except AppointmentCreationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="complete")
    def complete(self, request, pk=None):
        """Mark appointment as completed"""
        appointment_service = AppointmentBusinessService(request.tenant)

        try:
            appointment = appointment_service.complete_appointment(pk)
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        except AppointmentCreationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"], url_path="no-show")
    def no_show(self, request, pk=None):
        """Mark appointment as no-show"""
        appointment_service = AppointmentBusinessService(request.tenant)

        try:
            appointment = appointment_service.mark_no_show(pk)
            serializer = self.get_serializer(appointment)
            return Response(serializer.data)
        except AppointmentCreationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="ics")
    def export_ics(self, request, pk=None):
        """Export appointment as ICS calendar file"""
        appointment = self.get_object()

        ics_content = generate_ics(appointment)
        filename = generate_ics_filename(appointment)

        response = HttpResponse(ics_content, content_type="text/calendar")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


@api_view(["GET"])
@permission_classes([AllowAny])  # Public endpoint for widget
def available_slots(request):
    """
    Get available time slots for booking
    Public endpoint for booking widget
    """
    # Get tenant from request (set by middleware)
    if not hasattr(request, "tenant") or request.tenant is None:
        return Response(
            {"error": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Validate query params
    query_serializer = AvailableSlotsSerializer(data=request.query_params)
    query_serializer.is_valid(raise_exception=True)

    service_id = query_serializer.validated_data["service_id"]
    date = query_serializer.validated_data["date"]
    staff_id = query_serializer.validated_data.get("staff_id")

    # Generate slots
    slot_generator = SlotGenerator(request.tenant)
    slots = slot_generator.get_available_slots(
        service_id=str(service_id),
        date=date,
        staff_id=str(staff_id) if staff_id else None,
    )

    # Serialize slots
    slot_serializer = SlotSerializer(slots, many=True)

    return Response(
        {
            "date": date.strftime("%Y-%m-%d"),
            "service_id": str(service_id),
            "slots": slot_serializer.data,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])  # Public endpoint for widget
def create_appointment(request):
    """
    Create a new appointment
    Public endpoint for booking widget
    """
    # Get tenant from request
    if not hasattr(request, "tenant") or request.tenant is None:
        return Response(
            {"error": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Validate input
    create_serializer = AppointmentCreateSerializer(data=request.data)
    create_serializer.is_valid(raise_exception=True)

    # Extract data
    customer_data = {
        "name": create_serializer.validated_data["customer_name"],
        "phone": create_serializer.validated_data["customer_phone"],
        "email": create_serializer.validated_data.get("customer_email", ""),
    }

    staff_id = str(create_serializer.validated_data["staff_id"])
    service_ids = [str(sid) for sid in create_serializer.validated_data["service_ids"]]
    start_at = create_serializer.validated_data["start_at"]
    location_id = (
        str(create_serializer.validated_data["location_id"])
        if create_serializer.validated_data.get("location_id")
        else None
    )
    notes = create_serializer.validated_data.get("notes", "")
    source = create_serializer.validated_data.get("source", "WIDGET")

    # Create appointment
    appointment_service = AppointmentBusinessService(request.tenant)

    try:
        appointment = appointment_service.create_appointment(
            customer_data=customer_data,
            staff_id=staff_id,
            service_ids=service_ids,
            start_at=start_at,
            location_id=location_id,
            notes=notes,
            source=source,
        )

        # Serialize response
        serializer = AppointmentSerializer(appointment)

        return Response(
            {
                "message": "Appointment created successfully",
                "appointment": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    except AppointmentCreationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
