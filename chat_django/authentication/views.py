import json
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime
from .tokens import create_tokens, refresh_access_token

User = get_user_model()

def prepare_user_response(user, access_token, refresh_token):
    """Helper function to prepare consistent user response"""
    return JsonResponse({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': str(user.id),
            'email': user.email,
            'role': user.role,
            'available_models': json.loads(user.available_models)
        }
    })

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({
                    'error': 'Email and password are required'
                }, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'error': 'User with this email already exists'
                }, status=400)
            
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password
            )
            # Set available models
            user.set_available_models(settings.AVAILABLE_MODELS)
            
            # Create tokens
            access_token, refresh_token = create_tokens(user, request)
            
            return prepare_user_response(user, access_token, refresh_token)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({
                    'error': 'Email and password are required'
                }, status=400)
            
            user = authenticate(email=email, password=password)
            if not user:
                # Track failed login attempts
                try:
                    user = User.objects.get(email=email)
                    user.failed_login_attempts += 1
                    user.last_failed_login = datetime.utcnow()
                    user.save()
                except User.DoesNotExist:
                    pass
                    
                return JsonResponse({
                    'error': 'Invalid credentials'
                }, status=401)
            
            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.save()
            
            # Create tokens
            access_token, refresh_token = create_tokens(user, request)
            
            return prepare_user_response(user, access_token, refresh_token)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return JsonResponse({
                    'error': 'Refresh token is required'
                }, status=400)
            
            # Get new access token
            access_token = refresh_access_token(refresh_token)
            
            return JsonResponse({
                'access_token': access_token
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=401)