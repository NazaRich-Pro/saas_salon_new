"""
Audit logging service.
"""
import logging
from typing import Any, Dict, Optional

from apps.tenants.models import Tenant
from apps.users.models import User
from django.http import HttpRequest

from .models import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating audit log entries.
    """

    @staticmethod
    def log(
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user: Optional[User] = None,
        tenant: Optional[Tenant] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[HttpRequest] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            action: Action performed (from AuditLog.ACTION_* constants)
            entity_type: Type of entity affected (e.g., 'Appointment', 'User')
            entity_id: ID of affected entity
            user: User who performed the action
            tenant: Tenant context
            metadata: Additional context as dict
            request: HTTP request object for IP/user agent

        Returns:
            Created AuditLog instance
        """
        try:
            # Extract request details
            ip_address = None
            user_agent = ""

            if request:
                # Get IP address
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(",")[0].strip()
                else:
                    ip_address = request.META.get("REMOTE_ADDR")

                # Get user agent
                user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]

            # Create log entry
            audit_log = AuditLog.objects.create(
                tenant=tenant,
                user=user,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )

            logger.info(
                f"Audit log created: {action} on {entity_type} "
                f"by {user.email if user else 'System'}"
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't raise - audit failure shouldn't break the main flow
            return None

    @staticmethod
    def log_login(user: User, request: HttpRequest, success: bool = True):
        """Log user login attempt."""
        return AuditService.log(
            action=AuditLog.ACTION_LOGIN,
            entity_type="User",
            entity_id=str(user.id),
            user=user,
            metadata={"success": success},
            request=request,
        )

    @staticmethod
    def log_logout(user: User, request: HttpRequest):
        """Log user logout."""
        return AuditService.log(
            action=AuditLog.ACTION_LOGOUT,
            entity_type="User",
            entity_id=str(user.id),
            user=user,
            request=request,
        )

    @staticmethod
    def log_password_change(user: User, request: HttpRequest):
        """Log password change."""
        return AuditService.log(
            action=AuditLog.ACTION_PASSWORD_CHANGE,
            entity_type="User",
            entity_id=str(user.id),
            user=user,
            request=request,
        )

    @staticmethod
    def log_2fa_enable(user: User, request: HttpRequest):
        """Log 2FA enable."""
        return AuditService.log(
            action=AuditLog.ACTION_2FA_ENABLE,
            entity_type="User",
            entity_id=str(user.id),
            user=user,
            request=request,
        )

    @staticmethod
    def log_payment(
        payment_id: str, tenant: Tenant, user: User, amount: float, request: HttpRequest
    ):
        """Log payment action."""
        return AuditService.log(
            action=AuditLog.ACTION_PAYMENT,
            entity_type="Payment",
            entity_id=payment_id,
            user=user,
            tenant=tenant,
            metadata={"amount": amount},
            request=request,
        )

    @staticmethod
    def log_refund(
        payment_id: str, tenant: Tenant, user: User, amount: float, request: HttpRequest
    ):
        """Log refund action."""
        return AuditService.log(
            action=AuditLog.ACTION_REFUND,
            entity_type="Payment",
            entity_id=payment_id,
            user=user,
            tenant=tenant,
            metadata={"amount": amount},
            request=request,
        )

    @staticmethod
    def log_export(export_type: str, tenant: Tenant, user: User, request: HttpRequest):
        """Log data export."""
        return AuditService.log(
            action=AuditLog.ACTION_EXPORT,
            entity_type="Report",
            user=user,
            tenant=tenant,
            metadata={"export_type": export_type},
            request=request,
        )

    @staticmethod
    def log_impersonate(admin_user: User, target_user: User, request: HttpRequest):
        """Log impersonation (superadmin login as tenant admin)."""
        return AuditService.log(
            action=AuditLog.ACTION_IMPERSONATE,
            entity_type="User",
            entity_id=str(target_user.id),
            user=admin_user,
            metadata={
                "admin_email": admin_user.email,
                "target_email": target_user.email,
            },
            request=request,
        )
