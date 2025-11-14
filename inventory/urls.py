from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocationViewSet,
    ItemViewSet,
    StockTransactionViewSet,
    InventoryViewSet,
    TransactionJournalViewSet
)

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'transactions', StockTransactionViewSet, basename='transaction')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'journal', TransactionJournalViewSet, basename='journal')

urlpatterns = [
    path('', include(router.urls)),
]

