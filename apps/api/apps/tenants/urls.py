from django.urls import path

from . import views

urlpatterns = [
    # Registration (public)
    path("register-salon/", views.register_salon, name="register_salon"),
    path("register-solo/", views.register_solo, name="register_solo"),
    path("auto-login/", views.auto_login, name="auto_login"),
]
