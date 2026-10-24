from django.urls import path
from . import registration_views as views
from . import session_views as session_views

urlpatterns = [
    path("web/login/", session_views.web_login),
    path("mobile/login/", session_views.mobile_login),
    path("mobile/refresh/", session_views.refresh),
    path("me/", session_views.me),
    path("logout/", session_views.logout),
    path("logout-all/", session_views.logout_all),
    path("sessions/", session_views.session_list),
    path("sessions/<str:session_id>/", session_views.revoke),
    path("csrf/", views.csrf_bootstrap),
    path("registration/request/", views.registration_request),
    path("registration/confirm/", views.registration_confirm),
    path("registration/resend/", views.registration_resend),
    path("password-reset/request/", views.reset_request),
    path("password-reset/confirm/", views.reset_confirm),
    path("password-reset/resend/", views.reset_resend),
]
