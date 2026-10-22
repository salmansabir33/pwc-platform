import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Organization", fields=[
            ("id",models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False,serialize=False)),
            ("name",models.CharField(max_length=250)),
            ("city",models.CharField(max_length=100,blank=True)),
            ("classification",models.CharField(max_length=16,choices=[("registered","Registered"),("unregistered","Eligible unregistered")])),
            ("created_at",models.DateTimeField(auto_now_add=True))]),
        migrations.CreateModel(name="OrganizationWorkspace", fields=[
            ("id",models.BigAutoField(primary_key=True,serialize=False)),
            ("state",models.CharField(max_length=16,default="provisional",choices=[("provisional","Provisional"),("pending","Verification pending"),("verified","Verified"),("restricted","Restricted"),("deactivated","Deactivated")])),
            ("organization",models.OneToOneField(to="organizations.organization",related_name="workspace",on_delete=django.db.models.deletion.PROTECT))]),
        migrations.CreateModel(name="OrganizationAccess", fields=[
            ("id",models.BigAutoField(primary_key=True,serialize=False)),
            ("role",models.CharField(max_length=16,choices=[("claimant","Claimant"),("admin","Verified administrator"),("members","Member manager")])),
            ("active",models.BooleanField(default=True)),
            ("organization",models.ForeignKey(to="organizations.organization",on_delete=django.db.models.deletion.PROTECT)),
            ("user",models.ForeignKey(to=settings.AUTH_USER_MODEL,on_delete=django.db.models.deletion.PROTECT))]),
        migrations.AddConstraint(model_name="organizationaccess",constraint=models.UniqueConstraint(fields=["organization","user","role"],name="unique_org_user_role")),
    ]
