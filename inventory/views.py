from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from django.db.models import Max
from django.db import IntegrityError
from .models import Item, Location, StockTransaction, Inventory, TransactionJournal, UsedItem
from .serializers import (
    ItemSerializer,
    LocationSerializer,
    StockTransactionSerializer,
    InventorySerializer,
    TransactionJournalSerializer,
    UsedItemSerializer,
)
from .scraper import scrape_lego_product_info


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    
    def get_queryset(self):
        """Filter locations by current user"""
        return Location.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Associate location with current user"""
        serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        Override delete to handle inventory transfer.
        Transaction history is preserved via denormalized fields, so deletion is always allowed.
        """
        location = self.get_object()
        
        # Check if location has any NIB inventory or used items
        has_inventory = Inventory.objects.filter(
            user=request.user,
            location=location
        ).exclude(quantity=0).exists()

        has_used_items = UsedItem.objects.filter(
            user=request.user,
            location=location
        ).exists()
        
        # Get transfer_to_location_id if provided
        transfer_to_location_id = request.data.get('transfer_to_location_id')
        
        if has_inventory or has_used_items:
            if transfer_to_location_id:
                # Transfer inventory to another location
                try:
                    transfer_to_location = Location.objects.get(
                        id=transfer_to_location_id,
                        user=request.user
                    )
                    if transfer_to_location.id == location.id:
                        return Response(
                            {'error': 'Cannot transfer inventory to the same location'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Transfer used items to new location
                    UsedItem.objects.filter(
                        user=request.user,
                        location=location
                    ).update(location=transfer_to_location)

                    # Transfer all NIB inventory (user-specific)
                    inventories_to_transfer = Inventory.objects.filter(
                        user=request.user,
                        location=location
                    ).exclude(quantity=0)
                    for inv in inventories_to_transfer:
                        # Capture quantities before transfer
                        source_quantity_before = inv.quantity
                        source_quantity_after = 0
                        
                        # Get or create inventory at target location (user-specific)
                        target_inv, created = Inventory.objects.get_or_create(
                            user=request.user,
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
                            user=request.user,
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
                            user=request.user,
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
                # No transfer location specified — block deletion
                inventory_items = Inventory.objects.filter(
                    user=request.user,
                    location=location
                ).exclude(quantity=0)
                used_count = UsedItem.objects.filter(user=request.user, location=location).count()
                items_list = [f"{inv.item.item_id} ({inv.quantity})" for inv in inventory_items[:5]]
                items_text = ', '.join(items_list)
                if inventory_items.count() > 5:
                    items_text += f' and {inventory_items.count() - 5} more...'

                msg_parts = []
                if inventory_items.count():
                    msg_parts.append(f'{inventory_items.count()} NIB item(s) with stock')
                if used_count:
                    msg_parts.append(f'{used_count} used unit(s)')

                return Response(
                    {
                        'error': f'Cannot delete location "{location.name}" because it has inventory in stock.',
                        'has_inventory': True,
                        'inventory_count': inventory_items.count(),
                        'used_item_count': used_count,
                        'items': items_list,
                        'message': f'Location has {" and ".join(msg_parts)}: {items_text}. Please transfer inventory to another location first.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Transaction history is preserved via denormalized fields (location_name_str),
        # so we can safely delete the location even if it has transaction history.
        # The foreign key will be set to NULL, but the location name will remain in the journal.
        return super().destroy(request, *args, **kwargs)


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()  # Items are shared across users
    serializer_class = ItemSerializer

    def _fetch_product_info(self, item):
        """Fetch product info from web if not already present"""
        product_info = None
        if not item.name or not item.image_url:
            product_info = scrape_lego_product_info(item.item_id)
            if product_info:
                if product_info.get('name') and not item.name:
                    item.name = product_info['name']
                if product_info.get('image_url') and not item.image_url:
                    item.image_url = product_info['image_url']
                item.save()
        return product_info

    @action(detail=False, methods=['get', 'patch'], url_path='by-item-id/(?P<item_id>[^/.]+)')
    def by_item_id(self, request, item_id=None):
        """Get or update item by item_id"""
        try:
            item = Item.objects.get(item_id=item_id)
            
            if request.method == 'PATCH':
                # Update item (e.g., image_url)
                serializer = self.get_serializer(item, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                # Fetch product info to get updated image_options
                product_info = self._fetch_product_info(item)
                image_options = product_info.get('image_options') if product_info else None
                serializer = self.get_serializer(item, context={'image_options': image_options})
                return Response(serializer.data)
            else:
                # GET request
                product_info = self._fetch_product_info(item)
                # Get image_options from product_info if available
                image_options = product_info.get('image_options') if product_info else None
                serializer = self.get_serializer(item, context={'image_options': image_options})
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
        product_info = self._fetch_product_info(item)
        # Get image_options from product_info if available
        image_options = product_info.get('image_options') if product_info else None
        serializer = self.get_serializer(item, context={'image_options': image_options})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StockTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = StockTransactionSerializer
    
    def get_queryset(self):
        """Filter transactions by current user"""
        return StockTransaction.objects.filter(user=self.request.user)

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
            product_info = None
            if created or not item.name or not item.image_url:
                product_info = scrape_lego_product_info(item_id)
                if product_info:
                    if product_info.get('name') and not item.name:
                        item.name = product_info['name']
                    if product_info.get('image_url') and not item.image_url:
                        item.image_url = product_info['image_url']
                    item.save()

            # Get the location (user-specific)
            location = get_object_or_404(Location, id=location_id, user=request.user)

            # Create the transaction (associate with user)
            transaction = StockTransaction.objects.create(
                user=request.user,
                item=item,
                location=location,
                transaction_type=transaction_type,
                quantity=quantity
            )

            # Update inventory (user-specific)
            inventory, created = Inventory.objects.get_or_create(
                user=request.user,
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

            # Create journal entry with denormalized data (user-specific)
            try:
                TransactionJournal.objects.create(
                    user=request.user,
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
    serializer_class = InventorySerializer
    
    def get_queryset(self):
        """Filter inventory by current user"""
        return Inventory.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='by-item-id/(?P<item_id>[^/.]+)')
    def by_item_id(self, request, item_id=None):
        """Get inventory for a specific item (user-specific)"""
        try:
            item = Item.objects.get(item_id=item_id)
            inventory = Inventory.objects.filter(user=request.user, item=item)
            serializer = self.get_serializer(inventory, many=True)
            return Response(serializer.data)
        except Item.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TransactionJournalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionJournalSerializer
    
    def get_queryset(self):
        """Filter journal entries by current user"""
        return TransactionJournal.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_item(self, request):
        """Get journal entries for a specific item (user-specific)"""
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use denormalized field to find entries (works even if item deleted)
        journal_entries = TransactionJournal.objects.filter(
            user=request.user,
            item_id_str=item_id
        )
        serializer = self.get_serializer(journal_entries, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """Get journal entries for a specific location (user-specific)"""
        location_id = request.query_params.get('location_id')
        location_name = request.query_params.get('location_name')
        
        if location_id:
            # Get location name first, then filter by denormalized field
            try:
                location = Location.objects.get(id=location_id, user=request.user)
                journal_entries = TransactionJournal.objects.filter(
                    user=request.user,
                    location_name_str=location.name
                )
            except Location.DoesNotExist:
                return Response(
                    {'error': 'Location not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif location_name:
            # Filter directly by denormalized location name (user-specific)
            journal_entries = TransactionJournal.objects.filter(
                user=request.user,
                location_name_str=location_name
            )
        else:
            return Response(
                {'error': 'location_id or location_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(journal_entries, many=True)
        return Response(serializer.data)


class UsedItemViewSet(viewsets.ModelViewSet):
    serializer_class = UsedItemSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = UsedItem.objects.filter(user=self.request.user).select_related('item', 'location')
        item_id = self.request.query_params.get('item_id')
        if item_id:
            qs = qs.filter(item__item_id=item_id)
        return qs

    def create(self, request, *args, **kwargs):
        item_id = request.data.get('item_id', '').strip()
        location_id = request.data.get('location_id')
        notes = request.data.get('notes', '')

        if not item_id:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if '~' in item_id:
            return Response({'error': 'item_id must be a base LEGO set ID (no ~ character)'}, status=status.HTTP_400_BAD_REQUEST)
        if not location_id:
            return Response({'error': 'location_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create Item, trigger scraper as normal
        item, created = Item.objects.get_or_create(item_id=item_id)
        if created or not item.name or not item.image_url:
            product_info = scrape_lego_product_info(item_id)
            if product_info:
                if product_info.get('name') and not item.name:
                    item.name = product_info['name']
                if product_info.get('image_url') and not item.image_url:
                    item.image_url = product_info['image_url']
                item.save()

        location = get_object_or_404(Location, id=location_id, user=request.user)

        # Auto-assign suffix atomically
        try:
            with db_transaction.atomic():
                max_suffix = UsedItem.objects.filter(
                    user=request.user, item=item
                ).aggregate(Max('suffix'))['suffix__max'] or 0
                used_item = UsedItem.objects.create(
                    user=request.user,
                    item=item,
                    location=location,
                    suffix=max_suffix + 1,
                    notes=notes,
                )
        except IntegrityError:
            return Response(
                {'error': 'Failed to assign unit ID, please try again.'},
                status=status.HTTP_409_CONFLICT
            )

        # Journal entry: snapshot notes at receive time
        journal_notes = f"{used_item.used_item_id}: {notes}" if notes else used_item.used_item_id
        TransactionJournal.objects.create(
            user=request.user,
            item=item,
            location=location,
            item_id_str=item.item_id,
            item_name_str=item.name or '',
            location_name_str=location.name,
            transaction_type='RECEIVE',
            quantity=1,
            quantity_before=0,
            quantity_after=1,
            used_item_id_str=used_item.used_item_id,
            used_item_notes=notes,
            notes=journal_notes,
        )

        return Response(UsedItemSerializer(used_item).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        used_item = self.get_object()
        notes_changed = 'notes' in request.data and request.data['notes'] != used_item.notes
        old_notes = used_item.notes

        if 'notes' in request.data:
            used_item.notes = request.data['notes']
        if 'location_id' in request.data:
            location = get_object_or_404(Location, id=request.data['location_id'], user=request.user)
            used_item.location = location
        used_item.save()

        if notes_changed:
            new_notes = used_item.notes
            journal_notes = f"{used_item.used_item_id}: {new_notes}" if new_notes else used_item.used_item_id
            if old_notes:
                journal_notes += f" (was: {old_notes})"
            TransactionJournal.objects.create(
                user=request.user,
                item=used_item.item,
                location=used_item.location,
                item_id_str=used_item.item.item_id,
                item_name_str=used_item.item.name or '',
                location_name_str=used_item.location.name if used_item.location else '',
                transaction_type='EDIT',
                quantity=1,
                quantity_before=1,
                quantity_after=1,
                used_item_id_str=used_item.used_item_id,
                used_item_notes=new_notes,
                notes=journal_notes,
            )

        return Response(UsedItemSerializer(used_item).data)

    def destroy(self, request, *args, **kwargs):
        used_item = self.get_object()
        location = used_item.location
        journal_notes = f"{used_item.used_item_id}: {used_item.notes}" if used_item.notes else used_item.used_item_id
        TransactionJournal.objects.create(
            user=request.user,
            item=used_item.item,
            location=location,
            item_id_str=used_item.item.item_id,
            item_name_str=used_item.item.name or '',
            location_name_str=location.name if location else '',
            transaction_type='DELETE',
            quantity=1,
            quantity_before=1,
            quantity_after=0,
            used_item_id_str=used_item.used_item_id,
            used_item_notes=used_item.notes,
            notes=journal_notes,
        )
        used_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        used_item = self.get_object()
        location = used_item.location

        # Snapshot notes before deletion
        journal_notes = f"{used_item.used_item_id}: {used_item.notes}" if used_item.notes else used_item.used_item_id
        TransactionJournal.objects.create(
            user=request.user,
            item=used_item.item,
            location=location,
            item_id_str=used_item.item.item_id,
            item_name_str=used_item.item.name or '',
            location_name_str=location.name if location else '',
            transaction_type='SHIP',
            quantity=1,
            quantity_before=1,
            quantity_after=0,
            used_item_id_str=used_item.used_item_id,
            used_item_notes=used_item.notes,
            notes=journal_notes,
        )

        shipped_id = used_item.used_item_id
        used_item.delete()
        return Response({'shipped': shipped_id})

    @action(detail=False, methods=['get'], url_path='by-item-id/(?P<item_id>[^/.]+)')
    def by_item_id(self, request, item_id=None):
        qs = UsedItem.objects.filter(
            user=request.user, item__item_id=item_id
        ).select_related('item', 'location')
        return Response(UsedItemSerializer(qs, many=True).data)
