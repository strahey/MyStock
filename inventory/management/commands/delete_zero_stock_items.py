from django.core.management.base import BaseCommand
from inventory.models import Item, Inventory
from django.db.models import Sum


class Command(BaseCommand):
    help = 'Delete all items that have zero stock in all locations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        # Find items with zero stock using efficient query
        # Get all item IDs that have inventory with quantity > 0
        items_with_stock = Inventory.objects.values('item_id').annotate(
            total=Sum('quantity')
        ).filter(total__gt=0).values_list('item_id', flat=True)

        # Items to delete are those not in the list above
        # This includes items with no inventory records and items with only zero quantities
        items_to_delete = Item.objects.exclude(id__in=items_with_stock)
        count = items_to_delete.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No items with zero stock found.'))
            return

        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                f'⚠️  This will delete {count} item(s) with zero stock in all locations.'
            ))
            confirm = input('Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        # Get item IDs before deletion for reporting
        deleted_item_ids = list(items_to_delete.values_list('item_id', flat=True))
        
        # Delete the items
        items_to_delete.delete()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Successfully deleted {count} item(s) with zero stock:\n'
            f'   {", ".join(deleted_item_ids[:10])}'
            + (f'\n   ... and {count - 10} more' if count > 10 else '')
        ))

