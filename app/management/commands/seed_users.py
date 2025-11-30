from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed users into the database'

    def handle(self, *args, **kwargs):
        # Define user data
        users_data = [
            {
                'username': 'driver_user',
                'email': 'devsun36@gmail.com',
                'password': 'password123',
                'role': 'DRIVER',
                'group': 'Driver',
                'name': 'Driver User',
                'phone_number': '1234567890',
            },
            {
                'username': 'regular_user',
                'email': 'samuelmunyeke.2@gmail.com',
                'password': 'password123',
                'role': 'USER',
                'group': 'User',
                'name': 'Regular User',
                'phone_number': '0987654321',
            },
        ]

        for user_data in users_data:
            # Create user
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                defaults={
                    'name': user_data['name'],
                    'phone_number': user_data['phone_number'],
                }
            )
            if created:
                user.set_password(user_data['password'])  # Set password
                user.save()  # Save the user

                # Assign user to the specified group
                group = Group.objects.get(name=user_data['group'])
                user.groups.add(group)

                self.stdout.write(self.style.SUCCESS(f'User "{user_data["username"]}" created and added to group "{user_data["group"]}".'))
            else:
                self.stdout.write(self.style.WARNING(f'User "{user_data["username"]}" already exists.')) 