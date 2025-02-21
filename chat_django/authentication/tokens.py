"""Token handling utilities."""

import uuid
from datetime import datetime, timedelta
import jwt
from django.conf import settings
from .models import User

def create_tokens(user: User, request=None) -> tuple[str, str]:
    """Create access and refresh tokens for a user.
    
    Args:
        user: The user to create tokens for
        request: Optional request object to record IP
        
    Returns:
        Tuple of (access_token, refresh_token)
    """
    # Generate unique JTIs (JWT IDs)
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())
    
    # Create access token (short-lived)
    access_token = jwt.encode({
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'type': 'access',
        'jti': access_jti,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, settings.SECRET_KEY, algorithm='HS256')
    
    # Create refresh token (long-lived)
    refresh_token = jwt.encode({
        'user_id': str(user.id),
        'type': 'refresh',
        'jti': refresh_jti,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, settings.SECRET_KEY, algorithm='HS256')
    
    # Store refresh token JTI
    user.refresh_token_jti = refresh_jti
    if request and request.META.get('REMOTE_ADDR'):
        user.last_login_ip = request.META.get('REMOTE_ADDR')
    user.save()
    
    return access_token, refresh_token

def verify_token(token: str, token_type: str = 'access') -> dict:
    """Verify a token and return its payload.
    
    Args:
        token: The JWT token to verify
        token_type: Either 'access' or 'refresh'
        
    Returns:
        Dict containing the token payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid
        ValidationError: If token type doesn't match or user is inactive
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        # Verify token type
        if payload.get('type') != token_type:
            raise jwt.InvalidTokenError(f'Invalid token type. Expected {token_type}')
        
        # Get user and verify status
        user = User.objects.get(id=payload['user_id'])
        if not user.is_active:
            raise jwt.InvalidTokenError('User is inactive')
            
        # For refresh tokens, verify JTI matches
        if token_type == 'refresh' and payload['jti'] != user.refresh_token_jti:
            raise jwt.InvalidTokenError('Refresh token has been revoked')
            
        return payload
        
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError('Token has expired')
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f'Invalid token: {str(e)}')
    except User.DoesNotExist:
        raise jwt.InvalidTokenError('User not found')

def refresh_access_token(refresh_token: str) -> str:
    """Create a new access token using a refresh token.
    
    Args:
        refresh_token: The refresh token to use
        
    Returns:
        New access token
        
    Raises:
        jwt.InvalidTokenError: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(refresh_token, 'refresh')
    
    # Get user
    user = User.objects.get(id=payload['user_id'])
    
    # Create new access token
    access_token = jwt.encode({
        'user_id': str(user.id),
        'email': user.email,
        'role': user.role,
        'type': 'access',
        'jti': str(uuid.uuid4()),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, settings.SECRET_KEY, algorithm='HS256')
    
    return access_token

def revoke_refresh_token(user: User):
    """Revoke a user's refresh token by clearing the stored JTI."""
    user.refresh_token_jti = None
    user.save()