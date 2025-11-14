from django.core.management.base import BaseCommand
from inventory.models import TransactionJournal, StockTransaction, Inventory, Item, Location


class Command(BaseCommand):
    help = 'Clear all data from the database (items, locations, inventory, transactions, and journal entries)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                '⚠️  WARNING: This will delete ALL data including items, locations, inventory, and transaction history.'
            ))
            confirm = input('Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return

        # Delete all data (order matters due to foreign key constraints)
        journal_count = TransactionJournal.objects.count()
        transaction_count = StockTransaction.objects.count()
        inventory_count = Inventory.objects.count()
        item_count = Item.objects.count()
        location_count = Location.objects.count()

        TransactionJournal.objects.all().delete()
        StockTransaction.objects.all().delete()
        Inventory.objects.all().delete()
        Item.objects.all().delete()
        Location.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            f'✅ Successfully deleted all data:\n'
            f'   - {journal_count} journal entries\n'
            f'   - {transaction_count} transactions\n'
            f'   - {inventory_count} inventory records\n'
            f'   - {item_count} items\n'
            f'   - {location_count} locations'
        ))

