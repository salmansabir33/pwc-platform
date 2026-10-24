import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY must be set")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [
    s.strip()
    for s in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if s.strip()
]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "organizations",
    "access",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.session_middleware.PersonalSessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "pwc"),
        "USER": os.getenv("DB_USER", "pwc"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 15},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {
        "NAME": "accounts.validators.MaximumLengthValidator",
        "OPTIONS": {"max_length": 128},
    },
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
}

# PWC-03A.2 is synthetic-only and disabled by default. Never derive delivery
# encryption keys from database contents or silently fall back to SECRET_KEY.
PWC_AUTH_FLOWS_ENABLED = os.getenv("PWC_AUTH_FLOWS_ENABLED", "0") == "1"
PWC_AUTH_DELIVERY_MODE = "synthetic"
PWC_AUTH_LINK_ORIGIN = os.getenv("PWC_AUTH_LINK_ORIGIN", "https://pwc.invalid")
PWC_AUTH_ABUSE_KEY = os.getenv("PWC_AUTH_ABUSE_KEY", "")
PWC_AUTH_DELIVERY_ACTIVE_KEY = os.getenv("PWC_AUTH_DELIVERY_ACTIVE_KEY", "")
# Key ring supports reading old ciphertext while new intents use active key.
# JSON is deployment configuration, never a credential committed to source.
PWC_AUTH_DELIVERY_KEYS = json.loads(os.getenv("PWC_AUTH_DELIVERY_KEYS", "{}"))
PWC_AUTH_GLOBAL_SENDS_PER_HOUR = 100

# 03A.3: explicit synthetic activation and exact trusted direct-TLS portal map.
PWC_AUTH_SESSIONS_ENABLED = os.getenv("PWC_AUTH_SESSIONS_ENABLED", "0") == "1"
PWC_AUTH_SESSION_KEY = os.getenv("PWC_AUTH_SESSION_KEY", "")
PWC_AUTH_PORTALS = json.loads(os.getenv("PWC_AUTH_PORTALS", "{}"))
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "__Host-pwc_session"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_PATH = "/"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
AUTHENTICATION_BACKENDS = ["accounts.backends.VerifiedEmailBackend"]

# Separate default-off synthetic MFA switch and external factor encryption ring.
PWC_AUTH_MFA_ENABLED = os.getenv("PWC_AUTH_MFA_ENABLED", "0") == "1"
PWC_AUTH_MFA_ACTIVE_KEY = os.getenv("PWC_AUTH_MFA_ACTIVE_KEY", "")
PWC_AUTH_MFA_KEYS = json.loads(os.getenv("PWC_AUTH_MFA_KEYS", "{}"))
PWC_AUTH_MFA_PROOF_KEY = os.getenv("PWC_AUTH_MFA_PROOF_KEY", "")

# ADR-0002: independent default-off, isolated synthetic kernel. No NGO endpoints.
PWC_SYNTHETIC_AUTHORIZATION_ENABLED = os.getenv("PWC_SYNTHETIC_AUTHORIZATION_ENABLED", "0") == "1"
PWC_AUTHORIZATION_ENVIRONMENT = os.getenv("PWC_AUTHORIZATION_ENVIRONMENT", "disabled")
