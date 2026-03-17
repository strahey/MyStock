from django.contrib import admin
from .models import Location, Item, StockTransaction, Inventory, TransactionJournal, UsedItem


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_id', 'name', 'image_url', 'created_at', 'updated_at']
    search_fields = ['item_id', 'name']
    readonly_fields = ['created_at', 'updated_at', 'image_url']


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['item', 'location', 'transaction_type', 'quantity', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['item__item_id', 'location__name']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['item', 'location', 'quantity', 'updated_at']
    list_filter = ['location']
    search_fields = ['item__item_id', 'location__name']


@admin.register(UsedItem)
class UsedItemAdmin(admin.ModelAdmin):
    list_display = ['used_item_id', 'item', 'location', 'received_at', 'updated_at']
    search_fields = ['item__item_id', 'notes']
    list_filter = ['location', 'received_at']
    readonly_fields = ['received_at', 'updated_at']

    def used_item_id(self, obj):
        return obj.used_item_id
    used_item_id.short_description = 'Unit ID'


@admin.register(TransactionJournal)
class TransactionJournalAdmin(admin.ModelAdmin):
    list_display = ['item_id_str', 'item_name_str', 'location_name_str', 'transaction_type', 'quantity', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['item_id_str', 'item_name_str', 'location_name_str']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
