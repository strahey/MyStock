from rest_framework import serializers
from .models import Location, Item, StockTransaction, Inventory, TransactionJournal, UsedItem


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'created_at', 'updated_at']


class ItemSerializer(serializers.ModelSerializer):
    image_options = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = ['id', 'item_id', 'name', 'description', 'image_url', 'image_options', 'created_at', 'updated_at']
    
    def get_image_options(self, obj):
        """Get image_options from context if available"""
        return self.context.get('image_options', None)


class StockTransactionSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    item_id = serializers.CharField(write_only=True, required=True)
    location_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = StockTransaction
        fields = ['id', 'item', 'location', 'item_id', 'location_id', 'transaction_type', 'quantity', 'created_at']


class InventorySerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'item', 'location', 'quantity', 'created_at', 'updated_at']


class UsedItemSerializer(serializers.ModelSerializer):
    used_item_id = serializers.SerializerMethodField()
    item = ItemSerializer(read_only=True)
    location = LocationSerializer(read_only=True, allow_null=True)

    class Meta:
        model = UsedItem
        fields = ['id', 'used_item_id', 'item', 'location', 'suffix', 'notes', 'received_at', 'updated_at']
        read_only_fields = ['id', 'used_item_id', 'suffix', 'received_at', 'updated_at']

    def get_used_item_id(self, obj):
        return obj.used_item_id


class TransactionJournalSerializer(serializers.ModelSerializer):
    # Include both denormalized data and optional foreign key references
    item = ItemSerializer(read_only=True, allow_null=True)
    location = LocationSerializer(read_only=True, allow_null=True)
    
    # Expose denormalized fields with cleaner names for API
    item_id = serializers.CharField(source='item_id_str', read_only=True)
    item_name = serializers.CharField(source='item_name_str', read_only=True)
    location_name = serializers.CharField(source='location_name_str', read_only=True)

    class Meta:
        model = TransactionJournal
        fields = [
            'id', 'transaction', 'item', 'location',
            'item_id', 'item_name', 'location_name',
            'transaction_type', 'quantity', 'quantity_before', 'quantity_after',
            'used_item_id_str', 'used_item_notes',
            'reference_number', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'item_id', 'item_name', 'location_name']

