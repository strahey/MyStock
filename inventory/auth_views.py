from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
from rest_framework_simplejwt.tokens import RefreshToken
import requests

User = get_user_model()


class GoogleLoginView(APIView):
    """
    Initiate Google OAuth flow.
    Returns the Google OAuth URL to redirect the user to.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        import os
        from urllib.parse import urlencode

        client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID', '')
        if not client_id:
            return Response(
                {'error': 'Google OAuth not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Get the callback URL
        callback_url = request.build_absolute_uri('/api/auth/google/callback/')
        
        params = {
            'client_id': client_id,
            'redirect_uri': callback_url,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'online',
        }
        
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        return Response({
            'auth_url': google_auth_url,
            'redirect_uri': callback_url
        })


class GoogleCallbackView(APIView):
    """
    Handle Google OAuth callback and exchange code for tokens.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        if error:
            return Response(
                {'error': f'OAuth error: {error}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not code:
            return Response(
                {'error': 'Authorization code not provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Exchange code for tokens
        try:
            from django.conf import settings
            import os
            import requests
            
            client_id = os.getenv('GOOGLE_OAUTH2_CLIENT_ID', '')
            client_secret = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET', '')
            callback_url = request.build_absolute_uri('/api/auth/google/callback/')
            
            # Exchange authorization code for tokens
            token_url = 'https://oauth2.googleapis.com/token'
            token_data = {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': callback_url,
                'grant_type': 'authorization_code',
            }
            
            token_response = requests.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()
            
            access_token = tokens.get('access_token')
            id_token = tokens.get('id_token')
            
            # Get user info from Google
            user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            headers = {'Authorization': f'Bearer {access_token}'}
            user_info_response = requests.get(user_info_url, headers=headers)
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            
            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            google_id = user_info.get('id')
            
            if not email:
                return Response(
                    {'error': 'Email not provided by Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]  # Use email prefix as username
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
            
            # Create or update social account
            social_account, created = SocialAccount.objects.get_or_create(
                provider='google',
                uid=google_id,
                defaults={'user': user}
            )
            if not created:
                social_account.user = user
                social_account.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Return tokens (frontend will handle redirect)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'is_staff': user.is_staff,
                }
            })
            
        except requests.RequestException as e:
            return Response(
                {'error': f'Failed to exchange tokens: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleTokenLoginView(APIView):
    """
    Alternative endpoint: Exchange Google ID token for JWT tokens.
    This can be used if the frontend handles the OAuth flow directly.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('id_token')
        
        if not id_token:
            return Response(
                {'error': 'ID token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify ID token with Google
            import os
            import requests
            
            verify_url = 'https://oauth2.googleapis.com/tokeninfo'
            params = {'id_token': id_token}
            verify_response = requests.get(verify_url, params=params)
            verify_response.raise_for_status()
            token_info = verify_response.json()
            
            email = token_info.get('email')
            google_id = token_info.get('sub')
            
            if not email:
                return Response(
                    {'error': 'Email not found in token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create user
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=token_info.get('given_name', ''),
                    last_name=token_info.get('family_name', ''),
                )
            
            # Create or update social account
            social_account, created = SocialAccount.objects.get_or_create(
                provider='google',
                uid=google_id,
                defaults={'user': user}
            )
            if not created:
                social_account.user = user
                social_account.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'is_staff': user.is_staff,
                }
            })

        except Exception as e:
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DevLoginView(APIView):
    """
    Development-only login endpoint. Bypasses Google OAuth.
    Only available when DEBUG=True. DO NOT expose in production.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings
        if not settings.DEBUG:
            return Response(
                {'error': 'Not available in production'},
                status=status.HTTP_403_FORBIDDEN
            )

        email = request.data.get('email', '').strip()
        if not email or '@' not in email:
            return Response(
                {'error': 'Valid email required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user = User.objects.create_user(username=username, email=email)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'is_staff': user.is_staff,
            }
        })


class ImpersonateView(APIView):
    """
    Admin-only: issue a JWT scoped to another user.
    The original admin token is not modified; the frontend stores it separately.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        target_id = request.data.get('user_id')
        if not target_id:
            return Response(
                {'error': 'user_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            target = User.objects.get(pk=target_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if target.pk == request.user.pk:
            return Response(
                {'error': 'Cannot impersonate yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )

        refresh = RefreshToken.for_user(target)
        # Embed impersonated_by claim for audit purposes
        refresh['impersonated_by'] = request.user.id

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': target.id,
                'email': target.email,
                'first_name': target.first_name,
                'last_name': target.last_name,
                'username': target.username,
                'is_staff': target.is_staff,
            }
        })


class UserListView(APIView):
    """
    Admin-only: list all users for the impersonation picker.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )

        users = User.objects.exclude(pk=request.user.pk).order_by('email')
        return Response([
            {
                'id': u.id,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'username': u.username,
            }
            for u in users
        ])


class UserProfileView(APIView):
    """
    Get current user profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'is_staff': user.is_staff,
        })

