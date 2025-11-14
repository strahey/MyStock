from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Item, Location, StockTransaction, Inventory, TransactionJournal
from .serializers import (
    ItemSerializer,
    LocationSerializer,
    StockTransactionSerializer,
    InventorySerializer,
    TransactionJournalSerializer
)
from .scraper import scrape_lego_product_info


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    
    def destroy(self, request, *args, **kwargs):
        """
        Override delete to handle inventory transfer.
        Transaction history is preserved via denormalized fields, so deletion is always allowed.
        """
        location = self.get_object()
        
        # Check if location has any inventory
        has_inventory = Inventory.objects.filter(location=location).exclude(quantity=0).exists()
        
        # Get transfer_to_location_id if provided
        transfer_to_location_id = request.data.get('transfer_to_location_id')
        
        if has_inventory:
            if transfer_to_location_id:
                # Transfer inventory to another location
                try:
                    transfer_to_location = Location.objects.get(id=transfer_to_location_id)
                    if transfer_to_location.id == location.id:
                        return Response(
                            {'error': 'Cannot transfer inventory to the same location'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Transfer all inventory
                    inventories_to_transfer = Inventory.objects.filter(location=location).exclude(quantity=0)
                    for inv in inventories_to_transfer:
                        # Capture quantities before transfer
                        source_quantity_before = inv.quantity
                        source_quantity_after = 0
                        
                        # Get or create inventory at target location
                        target_inv, created = Inventory.objects.get_or_create(
                            item=inv.item,
                            location=transfer_to_location,
                            defaults={'quantity': 0}
                        )
                        target_quantity_before = target_inv.quantity
                        target_inv.quantity += inv.quantity
                        target_quantity_after = target_inv.quantity
                        target_inv.save()
                        
                        # Create journal entry for source location (decrease)
                        TransactionJournal.objects.create(
                            item=inv.item,  # Foreign key (may become null)
                            location=location,  # Foreign key (will become null after deletion)
                            item_id_str=inv.item.item_id,  # Denormalized
                            item_name_str=inv.item.name or '',  # Denormalized
                            location_name_str=location.name,  # Denormalized - preserves old location name
                            transaction_type='TRANSFER',
                            quantity=inv.quantity,
                            quantity_before=source_quantity_before,
                            quantity_after=source_quantity_after,
                            notes=f'Transferred to {transfer_to_location.name} (location deleted)',
                            reference_number=''
                        )
                        
                        # Create journal entry for target location (increase)
                        TransactionJournal.objects.create(
                            item=inv.item,  # Foreign key (may become null)
                            location=transfer_to_location,  # Foreign key (may become null)
                            item_id_str=inv.item.item_id,  # Denormalized
                            item_name_str=inv.item.name or '',  # Denormalized
                            location_name_str=transfer_to_location.name,  # Denormalized
                            transaction_type='TRANSFER',
                            quantity=inv.quantity,
                            quantity_before=target_quantity_before,
                            quantity_after=target_quantity_after,
                            notes=f'Transferred from {location.name} (location deleted)',
                            reference_number=''
                        )
                        
                        # Set source inventory to 0 (don't delete to preserve transaction history)
                        inv.quantity = 0
                        inv.save()
                    
                except Location.DoesNotExist:
                    return Response(
                        {'error': 'Transfer location not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # No transfer location specified, prevent deletion if there's inventory
                inventory_items = Inventory.objects.filter(location=location).exclude(quantity=0)
                items_list = [f"{inv.item.item_id} ({inv.quantity})" for inv in inventory_items[:5]]
                items_text = ', '.join(items_list)
                if inventory_items.count() > 5:
                    items_text += f' and {inventory_items.count() - 5} more...'
                
                return Response(
                    {
                        'error': f'Cannot delete location "{location.name}" because it has inventory in stock.',
                        'has_inventory': True,
                        'inventory_count': inventory_items.count(),
                        'items': items_list,
                        'message': f'Location has {inventory_items.count()} item(s) with stock: {items_text}. Please transfer inventory to another location or remove all stock first.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Transaction history is preserved via denormalized fields (location_name_str),
        # so we can safely delete the location even if it has transaction history.
        # The foreign key will be set to NULL, but the location name will remain in the journal.
        return super().destroy(request, *args, **kwargs)


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def _fetch_product_info(self, item):
        """Fetch product info from web if not already present"""
        if not item.name or not item.image_url:
            product_info = scrape_lego_product_info(item.item_id)
            if product_info:
                if product_info.get('name') and not item.name:
                    item.name = product_info['name']
                if product_info.get('image_url') and not item.image_url:
                    item.image_url = product_info['image_url']
                item.save()

    @action(detail=False, methods=['get'], url_path='by-item-id/(?P<item_id>[^/.]+)')
    def by_item_id(self, request, item_id=None):
        """Get item by item_id"""
        try:
            item = Item.objects.get(item_id=item_id)
            self._fetch_product_info(item)
            serializer = self.get_serializer(item)
            return Response(serializer.data)
        except Item.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request, *args, **kwargs):
        """Create item and fetch product info"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        self._fetch_product_info(item)
        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StockTransactionViewSet(viewsets.ModelViewSet):
    queryset = StockTransaction.objects.all()
    serializer_class = StockTransactionSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            item_id = serializer.validated_data.get('item_id')
            location_id = serializer.validated_data.get('location_id')
            transaction_type = serializer.validated_data.get('transaction_type')
            quantity = serializer.validated_data.get('quantity')
            
            if not item_id or not location_id:
                return Response(
                    {'error': 'item_id and location_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not transaction_type:
                return Response(
                    {'error': 'transaction_type is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not quantity or quantity <= 0:
                return Response(
                    {'error': 'quantity must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create the item
            item, created = Item.objects.get_or_create(item_id=item_id)

            # Fetch product info if this is a new item or info is missing
            if created or not item.name or not item.image_url:
                product_info = scrape_lego_product_info(item_id)
                if product_info:
                    if product_info.get('name') and not item.name:
                        item.name = product_info['name']
                    if product_info.get('image_url') and not item.image_url:
                        item.image_url = product_info['image_url']
                    item.save()

            # Get the location
            location = get_object_or_404(Location, id=location_id)

            # Create the transaction
            transaction = StockTransaction.objects.create(
                item=item,
                location=location,
                transaction_type=transaction_type,
                quantity=quantity
            )

            # Update inventory
            inventory, created = Inventory.objects.get_or_create(
                item=item,
                location=location,
                defaults={'quantity': 0}
            )

            # Capture quantity before transaction
            quantity_before = inventory.quantity

            if transaction_type == 'RECEIVE':
                inventory.quantity += quantity
            elif transaction_type == 'SHIP':
                if inventory.quantity < quantity:
                    return Response(
                        {'error': f'Insufficient stock. Available: {inventory.quantity}, Requested: {quantity}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                inventory.quantity -= quantity

            # Capture quantity after transaction
            quantity_after = inventory.quantity
            inventory.save()

            # Create journal entry with denormalized data
            try:
                TransactionJournal.objects.create(
                    transaction=transaction,
                    item=item,  # Foreign key for querying (may become null if item deleted)
                    location=location,  # Foreign key for querying (may become null if location deleted)
                    item_id_str=item.item_id,  # Denormalized: stored as string
                    item_name_str=item.name or '',  # Denormalized: stored as string
                    location_name_str=location.name,  # Denormalized: stored as string
                    transaction_type=transaction_type,
                    quantity=quantity,
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    notes='',  # Can be extended to accept notes from API
                    reference_number=''  # Can be extended to accept reference from API
                )
            except Exception as e:
                # If journal creation fails, log but don't fail the transaction
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to create journal entry: {str(e)}')

            response_serializer = StockTransactionSerializer(transaction)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            import sys
            error_details = traceback.format_exc()
            # In development, always show error details
            from django.conf import settings
            show_details = settings.DEBUG
            return Response(
                {
                    'error': f'Server error: {str(e)}',
                    'details': error_details if show_details else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    @action(detail=False, methods=['get'], url_path='by-item-id/(?P<item_id>[^/.]+)')
    def by_item_id(self, request, item_id=None):
        """Get inventory for a specific item"""
        try:
            item = Item.objects.get(item_id=item_id)
            inventory = Inventory.objects.filter(item=item)
            serializer = self.get_serializer(inventory, many=True)
            return Response(serializer.data)
        except Item.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TransactionJournalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TransactionJournal.objects.all()
    serializer_class = TransactionJournalSerializer

    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """Get journal entries for a specific item"""
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use denormalized field to find entries (works even if item deleted)
        journal_entries = TransactionJournal.objects.filter(item_id_str=item_id)
        serializer = self.get_serializer(journal_entries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get journal entries for a specific location"""
        location_id = request.query_params.get('location_id')
        location_name = request.query_params.get('location_name')
        
        if location_id:
            # Get location name first, then filter by denormalized field
            try:
                location = Location.objects.get(id=location_id)
                journal_entries = TransactionJournal.objects.filter(location_name_str=location.name)
            except Location.DoesNotExist:
                return Response(
                    {'error': 'Location not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif location_name:
            # Filter directly by denormalized location name
            journal_entries = TransactionJournal.objects.filter(location_name_str=location_name)
        else:
            return Response(
                {'error': 'location_id or location_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(journal_entries, many=True)
        return Response(serializer.data)
