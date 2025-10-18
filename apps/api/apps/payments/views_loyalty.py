"""Views for coupon and loyalty functionality"""
from decimal import Decimal

from apps.booking.models import Appointment, Customer
from apps.tenants.permissions import IsReception, IsTenantMember
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .birthday_service import BirthdayService
from .coupon_service import CouponApplicationError, CouponService
from .loyalty_service import LoyaltyService, LoyaltyServiceError


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsReception])
def apply_coupon(request):
    """
    Apply coupon to an appointment

    Request:
        {
            "appointment_id": "uuid",
            "coupon_code": "DISCOUNT50"
        }
    """
    appointment_id = request.data.get("appointment_id")
    coupon_code = request.data.get("coupon_code", "").strip().upper()

    if not appointment_id or not coupon_code:
        return Response(
            {"error": "appointment_id and coupon_code are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get appointment
    try:
        appointment = (
            Appointment.objects.select_related("customer")
            .prefetch_related("services")
            .get(id=appointment_id, tenant=request.tenant)
        )
    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Apply coupon
    coupon_service = CouponService(request.tenant)

    try:
        discount = coupon_service.apply_coupon_to_appointment(appointment, coupon_code)

        appointment.refresh_from_db()

        return Response(
            {
                "message": f"Купон {coupon_code} применен",
                "discount_kgs": str(discount),
                "original_price_kgs": str(appointment.total_price_kgs),
                "final_price_kgs": str(appointment.total_price_kgs - discount),
            },
            status=status.HTTP_200_OK,
        )

    except CouponApplicationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsReception])
def remove_coupon(request):
    """Remove coupon from appointment"""
    appointment_id = request.data.get("appointment_id")

    if not appointment_id:
        return Response(
            {"error": "appointment_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        appointment = Appointment.objects.get(id=appointment_id, tenant=request.tenant)
    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )

    coupon_service = CouponService(request.tenant)
    coupon_service.remove_coupon_from_appointment(appointment)

    return Response({"message": "Купон удален"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsReception])
def redeem_loyalty_points(request):
    """Redeem loyalty points for discount"""
    customer_id = request.data.get("customer_id")
    points_to_redeem = request.data.get("points_to_redeem")
    appointment_id = request.data.get("appointment_id")

    if not customer_id or not points_to_redeem:
        return Response(
            {"error": "customer_id and points_to_redeem are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        points_to_redeem = int(points_to_redeem)
    except (ValueError, TypeError):
        return Response(
            {"error": "points_to_redeem must be an integer"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        customer = Customer.objects.get(id=customer_id, tenant=request.tenant)
    except Customer.DoesNotExist:
        return Response(
            {"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND
        )

    appointment_total = None
    appointment = None

    if appointment_id:
        try:
            appointment = Appointment.objects.get(
                id=appointment_id, tenant=request.tenant, customer=customer
            )
            appointment_total = appointment.total_price_kgs
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
            )

    loyalty_service = LoyaltyService(request.tenant)

    try:
        result = loyalty_service.redeem_points(
            customer=customer,
            points_to_redeem=points_to_redeem,
            appointment_total=appointment_total or Decimal("999999.99"),
        )

        if appointment:
            appointment.discount_kgs += result["discount_kgs"]
            appointment.internal_notes = (
                f"Использовано {result['points_redeemed']} баллов\n"
                f"{appointment.internal_notes}"
            )
            appointment.save(
                update_fields=["discount_kgs", "internal_notes", "updated_at"]
            )

        return Response(
            {
                "message": "Баллы использованы успешно",
                **result,
                "discount_kgs": str(result["discount_kgs"]),
            },
            status=status.HTTP_200_OK,
        )

    except LoyaltyServiceError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def customer_loyalty_info(request, customer_id):
    """Get loyalty points information for customer"""
    try:
        customer = Customer.objects.get(id=customer_id, tenant=request.tenant)
    except Customer.DoesNotExist:
        return Response(
            {"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND
        )

    loyalty_service = LoyaltyService(request.tenant)

    if not loyalty_service.loyalty_rule:
        return Response(
            {"message": "Программа лояльности не активна"},
            status=status.HTTP_404_NOT_FOUND,
        )

    rule = loyalty_service.loyalty_rule
    points_value = loyalty_service.get_customer_points_value(customer)
    can_redeem = loyalty_service.can_redeem_points(customer, rule.min_points_to_redeem)

    return Response(
        {
            "customer_id": str(customer.id),
            "customer_name": customer.name,
            "loyalty_points": customer.loyalty_points,
            "points_value_kgs": str(points_value),
            "can_redeem": can_redeem,
            "min_points_to_redeem": rule.min_points_to_redeem,
            "earn_rate": f"{rule.earn_per_100_kgs} point(s) per 100 KGS",
            "redeem_rate": f"1 point = {rule.redeem_rate} KGS",
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def todays_birthdays(request):
    """Get customers with birthday today"""
    birthday_service = BirthdayService(request.tenant)
    customers = birthday_service.get_todays_birthdays()

    from apps.booking.serializers import CustomerSerializer

    serializer = CustomerSerializer(customers, many=True)

    return Response(
        {"count": len(customers), "customers": serializer.data},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def upcoming_birthdays(request):
    """Get customers with upcoming birthdays"""
    days = int(request.query_params.get("days", 7))
    days = min(days, 30)

    birthday_service = BirthdayService(request.tenant)
    customers = birthday_service.get_upcoming_birthdays(days_ahead=days)

    from apps.booking.serializers import CustomerSerializer

    serializer = CustomerSerializer(customers, many=True)

    return Response(
        {"days_ahead": days, "count": len(customers), "customers": serializer.data},
        status=status.HTTP_200_OK,
    )
