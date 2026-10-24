from django.urls import path
from . import registration_views as views
from . import session_views as session_views

from . import mfa_views

urlpatterns = [
    path("web/mfa/confirm/", mfa_views.endpoint("web_confirm")),
    path("mobile/mfa/confirm/", mfa_views.endpoint("mobile_confirm")),
    path("mfa/status/", mfa_views.endpoint("status")),
    path("mfa/enrollment/request/", mfa_views.endpoint("enroll")),
    path("mfa/enrollment/confirm/", mfa_views.endpoint("confirm")),
    path("mfa/remove/", mfa_views.endpoint("remove")),
    path("mfa/recovery-codes/rotate/", mfa_views.endpoint("rotate")),
    path("assurance/intents/", mfa_views.endpoint("intent")),
    path("step-up/", mfa_views.endpoint("step")),
    path("recovery-hold/clear/", mfa_views.endpoint("clear")),
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
