from django.urls import path
from . import registration_views as views

urlpatterns = [
    path("csrf/", views.csrf_bootstrap),
    path("registration/request/", views.registration_request),
    path("registration/confirm/", views.registration_confirm),
    path("registration/resend/", views.registration_resend),
    path("password-reset/request/", views.reset_request),
    path("password-reset/confirm/", views.reset_confirm),
    path("password-reset/resend/", views.reset_resend),
]
