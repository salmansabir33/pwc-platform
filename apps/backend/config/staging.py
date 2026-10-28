"""Deployment-only disabled-service profile; no proxy trust or activation switch."""

from .settings import *  # noqa: F403

if PWC_ENVIRONMENT != "staging":  # noqa: F405
    raise RuntimeError("Staging image requires staging profile")
SECURE_PROXY_SSL_HEADER = None
USE_X_FORWARDED_HOST = False
USE_X_FORWARDED_PORT = False
# Request/error payloads must not enter container logs. Health/exit status is the
# operational signal; review a privacy-safe observability extension before live use.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "CRITICAL"},
    "loggers": {"django": {"handlers": ["null"], "propagate": False}},
}
