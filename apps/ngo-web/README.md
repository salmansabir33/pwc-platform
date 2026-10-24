# NGO Web Portal — W1 foundation

Independent React/TypeScript/Vite entry point. From the repository root:

```bash
npm ci --ignore-scripts
npm run dev:ngo
npm run build -w @pwc/ngo-web
```

Only foundation overview, accessibility/language specimen and interface-state routes exist. No live authentication, real NGO context, data or business commands. Runtime networking is disabled in source, not enabled by environment variables. Canonical screen references are readiness labels, not implemented workflows.

See [W1 runbook](../../docs/runbooks/PWC-W1-WEB-FOUNDATION.md) for tests, preview-host configuration, security boundaries and W2/W3 dependencies.
