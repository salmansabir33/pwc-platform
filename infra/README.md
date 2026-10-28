Development compose config lives at repository root. Production deployment, private file storage, backups, and restore drills remain unimplemented. Never use dev server or sample credentials in production.

The [web-auth ingress acceptance handoff](web-auth/README.md) provides the operator-input procedure and credential-free observation tool. It does not configure a provider, enable production authentication or accept any actual host.
