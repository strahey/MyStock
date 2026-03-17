from django.db import models
from django.contrib.auth.models import User


class Location(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']  # Location names unique per user


class Item(models.Model):
    item_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, max_length=500, help_text="URL to product image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_id} - {self.name or 'Unnamed'}"

    class Meta:
        ordering = ['item_id']


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('RECEIVE', 'Receive'),
        ('SHIP', 'Ship'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} of {self.item.item_id} at {self.location.name}"


class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='inventory')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'item', 'location']  # Unique per user
        ordering = ['item', 'location']

    def __str__(self):
        return f"{self.item.item_id} at {self.location.name}: {self.quantity}"


class UsedItem(models.Model):
    """
    A single physical second-hand unit of a LEGO set.
    Identified as {item_id}~{suffix}, e.g. "10317~1".
    When shipped, this record is deleted; history is preserved in TransactionJournal.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='used_items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='used_items')
    location = models.ForeignKey(
        'Location', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='used_items'
    )
    suffix = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'item', 'suffix']
        ordering = ['item', 'suffix']

    @property
    def used_item_id(self):
        return f"{self.item.item_id}~{self.suffix}"

    def __str__(self):
        return self.used_item_id


class TransactionJournal(models.Model):
    """
    Comprehensive journal/audit log of all transactions.
    This provides a complete history of all stock movements.
    
    Data is denormalized (stored as strings) to preserve historical accuracy
    even if items or locations are deleted.
    """
    TRANSACTION_TYPES = [
        ('RECEIVE', 'Receive'),
        ('SHIP', 'Ship'),
        ('TRANSFER', 'Transfer'),
        ('EDIT', 'Edit'),
        ('DELETE', 'Delete'),
    ]

    # User who created this transaction
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    
    # Link to the original transaction (if applicable) - nullable for historical integrity
    transaction = models.ForeignKey(
        StockTransaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='journal_entries'
    )
    
    # Denormalized transaction details (stored at time of transaction)
    # These are the source of truth for historical records
    # Using different names to avoid conflict with ForeignKey's auto-generated _id fields
    item_id_str = models.CharField(max_length=100, db_index=True, help_text="Item ID at time of transaction (denormalized)")
    item_name_str = models.CharField(max_length=200, blank=True, help_text="Item name at time of transaction (denormalized)")
    location_name_str = models.CharField(max_length=100, db_index=True, help_text="Location name at time of transaction (denormalized)")
    
    # Optional foreign keys for querying (nullable to allow deletion of items/locations)
    item = models.ForeignKey(
        Item, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='journal_entries',
        help_text="Reference to item (may be null if item deleted)"
    )
    location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='journal_entries',
        help_text="Reference to location (may be null if location deleted)"
    )
    
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    
    # Inventory state before and after transaction
    quantity_before = models.IntegerField(help_text="Quantity at location before this transaction")
    quantity_after = models.IntegerField(help_text="Quantity at location after this transaction")
    
    # Used item fields (null for NIB transactions)
    used_item_id_str = models.CharField(max_length=120, blank=True, help_text="Used item compound ID at time of transaction, e.g. '10317~1'")
    used_item_notes = models.TextField(blank=True, help_text="Snapshot of used item condition notes at time of transaction")

    # Additional metadata
    notes = models.TextField(blank=True, help_text="Optional notes about this transaction")
    reference_number = models.CharField(max_length=100, blank=True, help_text="External reference number (PO, invoice, etc.)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['item_id_str', 'location_name_str']),
            models.Index(fields=['transaction_type']),
        ]
        verbose_name = "Transaction Journal Entry"
        verbose_name_plural = "Transaction Journal Entries"

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} of {self.item_id_str} at {self.location_name_str} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_quantity_change(self):
        """Returns the net change in quantity (positive for receive, negative for ship)"""
        if self.transaction_type == 'RECEIVE':
            return self.quantity
        else:
            return -self.quantity
