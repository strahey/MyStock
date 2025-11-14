from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from inventory.models import Item


class Command(BaseCommand):
    help = 'Delete a specific item from the database by item_id'

    def add_arguments(self, parser):
        parser.add_argument(
            'item_id',
            type=str,
            help='The item_id of the item to delete',
        )

    def handle(self, *args, **options):
        item_id = options['item_id']

        try:
            item = Item.objects.get(item_id=item_id)
            item_id_str = item.item_id
            item_name = item.name or 'Unnamed'
            
            # Delete the item (cascades to related records)
            item.delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ Successfully deleted item: {item_id_str} - {item_name}'
            ))
        except ObjectDoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'❌ Item with item_id "{item_id}" not found.'
            ))

