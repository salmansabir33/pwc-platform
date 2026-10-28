import ssl

bind = "0.0.0.0:8443"
workers = 2
threads = 2
worker_class = "gthread"
timeout = 30
graceful_timeout = 30
certfile = "/run/secrets/app_cert"
keyfile = "/run/secrets/app_key"
ca_certs = "/run/secrets/client_ca"
cert_reqs = ssl.CERT_REQUIRED
ssl_version = ssl.PROTOCOL_TLS_SERVER
# Genuine socket TLS determines WSGI scheme. Never accept header-derived HTTPS.
forwarded_allow_ips = ""
secure_scheme_headers = {}
accesslog = None
errorlog = "/dev/null"
capture_output = False


def ssl_context(conf, default_ssl_context_factory):
    context = default_ssl_context_factory()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context
