"""Deterministic PUBLIC fixture only, guarded to disposable test database names.

No users, officers, invitations, claims, consent or grants are provisioned.
"""
import os
import uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()
from django.conf import settings
from django.db import connection, transaction
from organizations.models import Organization, OrganizationWorkspace

if not (settings.PWC_ENVIRONMENT == 'test' and connection.vendor == 'postgresql'
        and str(connection.settings_dict['NAME']).startswith('pwc_synthetic_')):
    raise SystemExit('Public fixtures require isolated test PostgreSQL')
with transaction.atomic():
    for n in range(25):
        pk = uuid.UUID(int=9000+n)
        organization, _ = Organization.objects.update_or_create(
            pk=pk,
            defaults={'name': f'Synthetic Directory NGO {n:02}', 'city': 'Faisalabad', 'classification': 'registered'},
        )
        OrganizationWorkspace.objects.update_or_create(organization=organization, defaults={'state': 'verified' if n < 23 else 'restricted'})
print('Seeded 23 public / 2 restricted synthetic projection fixtures; no authority.')
