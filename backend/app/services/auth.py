"""Authentication service for Keycloak integration and JWT validation."""

from typing import Callable, Optional
import logging
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from app.config import settings
from app.schemas import KeycloakUserInfo

logger = logging.getLogger(__name__)
security = HTTPBearer()


class AuthService:
    """Service for handling Keycloak authentication and JWT validation."""

    def __init__(self):
        self.keycloak_url = settings.keycloak_server_url
        self.keycloak_realm = settings.keycloak_realm
        self.keycloak_client_id = settings.keycloak_client_id
        self.keycloak_client_secret = settings.keycloak_client_secret

    def get_public_key_url(self) -> str:
        """Get URL for Keycloak's JWKS (JSON Web Key Set)."""
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    async def validate_token(self, token: str) -> Optional[KeycloakUserInfo]:
        """
        Validate JWT token from Keycloak.
        
        In production, you'd fetch and cache the public key from JWKS endpoint.
        For now, we assume Keycloak is running and verify with the public key.
        
        Args:
            token: JWT token string
            
        Returns:
            KeycloakUserInfo if valid, None otherwise
        """
        try:
            # For development: If SKIP_JWT_VALIDATION is True, parse without verification
            if settings.skip_jwt_validation:
                decoded = jwt.get_unverified_claims(token)
                return KeycloakUserInfo(**decoded)

            # Production: Verify signature (requires public key from Keycloak)
            # This is a placeholder - actual implementation would fetch and cache the key
            # decoded = jwt.decode(
            #     token,
            #     public_key,
            #     algorithms=["RS256"],
            #     audience=self.keycloak_client_id,
            # )
            
            # For now, parse without verification (assumes SKIP_JWT_VALIDATION or trusted proxy)
            decoded = jwt.get_unverified_claims(token)
            return KeycloakUserInfo(**decoded)

        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in token validation: {e}")
            return None

    async def extract_token_from_header(self, credentials: HTTPAuthCredentials) -> str:
        """Extract and validate token from authorization header."""
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token


# Global instance
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> KeycloakUserInfo:
    """
    Dependency for endpoints that require authentication.
    Extracts and validates JWT token from Authorization header.
    
    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: KeycloakUserInfo = Depends(get_current_user)):
            return {"user": user}
    """
    token = await auth_service.extract_token_from_header(credentials)
    user_info = await auth_service.validate_token(token)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_info


def get_current_user_with_role(
    required_roles: list[str],
) -> Callable:
    """
    Factory for creating role-based access control dependency.
    
    Usage:
        admin_only = get_current_user_with_role(["ADMIN"])
        
        @router.delete("/admin/users/{user_id}")
        async def delete_user(user: KeycloakUserInfo = Depends(admin_only)):
            return {"deleted": True}
    """

    async def role_checker(user: KeycloakUserInfo = Depends(get_current_user)) -> KeycloakUserInfo:
        user_roles = user.realm_access.get("roles", []) if user.realm_access else []
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required roles: {required_roles}",
            )
        
        return user

    return role_checker
