from django.core.management.base import BaseCommand
from inventory.models import Location


class Command(BaseCommand):
    help = 'Seed initial locations'

    def handle(self, *args, **options):
        locations = ['Tull', 'Duck']
        
        for location_name in locations:
            location, created = Location.objects.get_or_create(name=location_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created location: {location_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Location "{location_name}" already exists'))

