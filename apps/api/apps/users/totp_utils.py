"""2FA TOTP utilities"""
import base64
import io

import pyotp
import qrcode
from django.conf import settings


def generate_totp_secret():
    """
    Generate a new TOTP secret

    Returns: base32 encoded secret string
    """
    return pyotp.random_base32()


def get_totp_uri(user, secret):
    """
    Generate TOTP provisioning URI for QR code

    Args:
        user: User instance
        secret: TOTP secret

    Returns: provisioning URI string
    """
    totp = pyotp.TOTP(secret)
    issuer_name = "BeautyHub"
    account_name = user.email

    return totp.provisioning_uri(name=account_name, issuer_name=issuer_name)


def generate_qr_code(uri):
    """
    Generate QR code image from URI

    Args:
        uri: TOTP provisioning URI

    Returns: base64 encoded PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


def verify_totp_code(secret, code):
    """
    Verify TOTP code

    Args:
        secret: TOTP secret
        code: 6-digit code from user

    Returns: Boolean
    """
    totp = pyotp.TOTP(secret)

    # Allow 1 time step before and after (30 seconds window)
    return totp.verify(code, valid_window=1)


def get_backup_codes(count=10):
    """
    Generate backup codes for 2FA

    Args:
        count: Number of backup codes to generate

    Returns: List of backup codes
    """
    import secrets
    import string

    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )
        # Format as XXXX-XXXX
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)

    return codes


def setup_2fa_for_user(user):
    """
    Setup 2FA for a user

    Args:
        user: User instance

    Returns: Dict with secret, qr_code, backup_codes
    """
    # Generate secret
    secret = generate_totp_secret()

    # Generate QR code
    uri = get_totp_uri(user, secret)
    qr_code = generate_qr_code(uri)

    # Generate backup codes
    backup_codes = get_backup_codes()

    # Save secret to user (but don't enable yet)
    user.twofa_secret = secret
    user.save(update_fields=["twofa_secret"])

    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "uri": uri,
    }


def enable_2fa_for_user(user, verification_code):
    """
    Enable 2FA for user after verifying setup code

    Args:
        user: User instance
        verification_code: 6-digit code to verify

    Returns: Boolean (success)
    """
    if not user.twofa_secret:
        return False

    # Verify the code
    if not verify_totp_code(user.twofa_secret, verification_code):
        return False

    # Enable 2FA
    user.twofa_enabled = True
    user.save(update_fields=["twofa_enabled"])

    return True


def disable_2fa_for_user(user):
    """
    Disable 2FA for user

    Args:
        user: User instance
    """
    user.twofa_enabled = False
    user.twofa_secret = None
    user.save(update_fields=["twofa_enabled", "twofa_secret"])


def requires_2fa(user):
    """
    Check if user requires 2FA

    Args:
        user: User instance

    Returns: Boolean
    """
    # Superadmins always require 2FA if enabled
    if user.is_superadmin:
        return user.twofa_enabled

    # Check if user is salon admin in any tenant
    from apps.tenants.models import Membership

    has_admin_role = Membership.objects.filter(
        user=user, role="SALON_ADMIN", is_active=True
    ).exists()

    if has_admin_role:
        return user.twofa_enabled

    return False
