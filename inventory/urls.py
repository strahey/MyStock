from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LocationViewSet,
    ItemViewSet,
    StockTransactionViewSet,
    InventoryViewSet,
    TransactionJournalViewSet
)
from .auth_views import (
    GoogleLoginView,
    GoogleCallbackView,
    GoogleTokenLoginView,
    DevLoginView,
    ImpersonateView,
    UserListView,
    UserProfileView
)

router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'transactions', StockTransactionViewSet, basename='transaction')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'journal', TransactionJournalViewSet, basename='journal')

urlpatterns = [
    path('', include(router.urls)),
    # Authentication endpoints
    path('auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('auth/google/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    path('auth/login/', GoogleTokenLoginView.as_view(), name='token_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', UserProfileView.as_view(), name='user_profile'),
    path('auth/dev-login/', DevLoginView.as_view(), name='dev_login'),
    path('auth/impersonate/', ImpersonateView.as_view(), name='impersonate'),
    path('auth/users/', UserListView.as_view(), name='user_list'),
]

