from django.core.management.base import BaseCommand
from control_center.models import User
import os

class Command(BaseCommand):
    help = 'Create a admin user in Control center, Grafana and InfluxDB'

    def handle(self, *args, **kwargs):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin')

        if not User.objects.filter(username=username).exists():
            user = User(username=username, is_superuser = True, is_staff = True)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists'))
