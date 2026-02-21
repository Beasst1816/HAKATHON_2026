from django.core.management.base import BaseCommand
from fleet.models import User


class Command(BaseCommand):
    help = 'Create sample FleetFlow users'

    def handle(self, *args, **options):
        users_data = [
            ('manager@fleetflow.com', 'Fleet Manager', User.Role.FLEET_MANAGER),
            ('dispatcher@fleetflow.com', 'Dispatcher', User.Role.DISPATCHER),
            ('safety@fleetflow.com', 'Safety Officer', User.Role.SAFETY_OFFICER),
            ('finance@fleetflow.com', 'Financial Analyst', User.Role.FINANCIAL_ANALYST),
        ]
        
        for email, name, role in users_data:
            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': name.split()[0],
                    'last_name': name.split()[-1] if len(name.split()) > 1 else '',
                    'role': role
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user {email}'))
            else:
                self.stdout.write(f'User {email} already exists')
        
        self.stdout.write(self.style.SUCCESS('\nDone! Login with email and password: password123'))
