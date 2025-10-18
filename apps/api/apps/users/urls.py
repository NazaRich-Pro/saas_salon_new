from django.urls import path

from . import views

urlpatterns = [
    # Health check
    path("health/", views.health_check, name="health_check"),
    # Authentication
    path("login/", views.login, name="login"),
    path("2fa/verify/", views.verify_2fa, name="verify_2fa"),
    path("refresh/", views.refresh, name="refresh"),
    path("logout/", views.logout, name="logout"),
    # Profile
    path("profile/", views.profile, name="profile"),
    path("password/change/", views.change_password, name="change_password"),
    # 2FA Management
    path("2fa/setup/", views.setup_2fa, name="setup_2fa"),
    path("2fa/enable/", views.enable_2fa, name="enable_2fa"),
    path("2fa/disable/", views.disable_2fa, name="disable_2fa"),
    # Device Sessions
    path("sessions/", views.device_sessions, name="device_sessions"),
    path(
        "sessions/<uuid:session_id>/terminate/",
        views.terminate_session,
        name="terminate_session",
    ),
]
