import json

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """
    Generate JWT tokens for a user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    """
    Login view to authenticate a user and return JWT tokens.
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                'status': 'error',
                'message': 'Username and password are required.'
            }, status=400)

        user = authenticate(username=username, password=password)
        if user is not None:
            tokens = get_tokens_for_user(user)
            return JsonResponse({
                'status': 'success',
                'message': f'Welcome back, {username}!',
                'tokens': tokens
            })
        elif user and user.is_active:
            return JsonResponse({
                'status': 'error',
                'message': 'Please verify your email account.'
            }, status=400)

        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password.'
            }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data.'
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def register_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password1 = data.get('password1')
        password2 = data.get('password2')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        if not email.endswith('@gmail.com'):
            return JsonResponse({'status': 'error', 'message': 'Only Gmail addresses are supported.'}, status=400)

        if not username or not password1 or not password2:
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)

        if password1 != password2:
            return JsonResponse({'status': 'error', 'message': 'Passwords do not match.'}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists.'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Email already registered with another user.'}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password1, first_name=first_name,
                                        last_name=last_name, is_active=False)

        # Create verification URL
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = f"{settings.FRONTEND_URL}/api/verify-email/{uid}/{token}/"

        # Send Email
        send_mail(
            subject='Verify your Medical Portal account',
            message=f"Hi {first_name},\n\nClick the link to verify your email:\n{verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return JsonResponse({'status': 'success', 'message': 'Registration successful! Check your Gmail to verify.'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """
    Logout view to blacklist the refresh token.
    """
    try:
        data = json.loads(request.body)
        refresh_token = data.get('refresh')

        if not refresh_token:
            return JsonResponse({
                'status': 'error',
                'message': 'Refresh token is required.'
            }, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return JsonResponse({
                'status': 'success',
                'message': 'Logout successful.'
            })
        except TokenError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid or expired refresh token.'
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data.'
        }, status=400)


class UserViewSet(ModelViewSet):
    """
    A ModelViewSet for user-related actions.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="get-user-info")
    def get_user_info(self, request):
        """
        Retrieve the authenticated user's username, first name, and last name.
        """
        user = request.user
        return Response({
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        })

    @action(detail=False, methods=["POST"], url_path="update-profile")
    def update_profile(self, request):
        """
        Update user profile details such as password, first_name, and last_name.
        """
        try:
            data = json.loads(request.body)
            user = request.user

            if not user.is_authenticated:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User is not authenticated.'
                }, status=401)

            # Update password
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            confirm_password = data.get('confirm_password')

            if current_password and new_password and confirm_password:
                if not user.check_password(current_password):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Current password is incorrect.'
                    }, status=400)
                if new_password != confirm_password:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'New passwords do not match.'
                    }, status=400)
                user.set_password(new_password)

            # Save changes
            user.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Profile updated successfully.'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data.'
            }, status=400)

# views.py

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import User
from django.http import JsonResponse

def verify_email(request, uidb64, token):
    try:
        # Decode the UID
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return JsonResponse({'status': 'success', 'message': 'Email verified successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid or expired token.'}, status=400)

    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return JsonResponse({'status': 'error', 'message': 'Invalid verification link.'}, status=400)
