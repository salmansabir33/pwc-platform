Development compose config lives at repository root. Production deployment, private file storage, backups, and restore drills remain unimplemented. Never use dev server or sample credentials in production.

The [web-auth ingress acceptance handoff](web-auth/README.md) provides the operator-input procedure and credential-free observation tool. It does not configure a provider, enable production authentication or accept any actual host.

The [disabled-service staging foundation](staging/README.md) now supplies separate
Compose builds, genuine application TLS, private PostgreSQL, operational scripts
and synthetic backup/restore tests. This is infrastructure evidence only: no
actual staging deployment, independently accepted hosts or credential-transport
authorization is implied. Production/private-file-storage readiness is unchanged.
