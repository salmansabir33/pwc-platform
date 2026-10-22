# ADR-0001 — New standalone PWC monorepo
Status: provisional engineering recommendation adopted as starter structure, not production approval.

- Repository working name: `pwc-platform`; dedicated to PWC, separate from Coventure.
- Modular Django/DRF/PostgreSQL backend skeleton, Flutter directory reserved, independent NGO web and PWC operations directories reserved.
- M1 first; M2 and M3 after tested isolation and authorization groundwork.
- Django/DRF, Flutter, hosting and exact admin-web technologies still require technical sign-off.
- Separate PWC alliance roles from organization-private roles; no default finance read for platform/alliance users.
