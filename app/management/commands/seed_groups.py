from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Seed groups into the database'

    def handle(self, *args, **kwargs):
        groups = ['Admin', 'User', 'Driver','Business']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created.'))
            else:
                self.stdout.write(self.style.WARNING(f'Group "{group_name}" already exists.')) 