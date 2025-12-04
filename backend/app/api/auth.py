"""Authentication and authorization helpers for the dashboard API.

Supports JWT-based authentication with role-based access control.
For local development, supports bypassing auth via environment variable.
"""
import os
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError, DecodeError

# Security scheme for JWT Bearer tokens
security = HTTPBearer(auto_error=False)

# Role types
Role = str
ROLE_READ_ONLY = "read-only"
ROLE_ADMIN = "admin"


class User:
    """Represents an authenticated user with a role."""

    def __init__(self, user_id: str, role: Role):
        self.user_id = user_id
        self.role = role

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == ROLE_ADMIN

    def can_access_admin_features(self) -> bool:
        """Check if user can access admin-only features."""
        return self.is_admin()


def get_jwt_secret() -> Optional[str]:
    """Get JWT secret from environment or return None."""
    return os.environ.get("JWT_SECRET")


def get_dev_auth_bypass() -> bool:
    """Check if dev auth bypass is enabled (local development only)."""
    return os.environ.get("DEV_AUTH_BYPASS", "").lower() in ("true", "1", "yes")


def decode_jwt_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload as dict

    Raises:
        HTTPException: If token is invalid or cannot be decoded
    """
    secret = get_jwt_secret()
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="JWT_SECRET not configured. Cannot validate tokens.",
        )

    try:
        # Decode token with secret
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except (InvalidTokenError, DecodeError) as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
        )


def extract_role_from_token(payload: dict) -> Role:
    """Extract role from JWT token payload.

    Looks for 'role' claim in the token. Defaults to 'read-only' if not present.

    Args:
        payload: Decoded JWT payload

    Returns:
        User role (read-only or admin)
    """
    # Common JWT role claim names
    role = (
        payload.get("role")
        or payload.get("user_role")
        or payload.get("https://claims.example.com/role")
    )
    if role not in (ROLE_READ_ONLY, ROLE_ADMIN):
        # Default to read-only for safety
        return ROLE_READ_ONLY
    return role


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> User:
    """Dependency to get the current authenticated user.

    Supports:
    1. JWT token in Authorization header (production)
    2. Dev auth bypass via DEV_AUTH_BYPASS env var (local dev only)

    Args:
        credentials: Optional HTTP Bearer credentials from request header

    Returns:
        User object with user_id and role

    Raises:
        HTTPException: If authentication fails
    """
    # Dev bypass for local development
    if get_dev_auth_bypass():
        # Return a default admin user for dev
        return User(user_id="dev-user", role=ROLE_ADMIN)

    # Production: require JWT token
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide a Bearer token in Authorization header.",
        )

    token = credentials.credentials
    payload = decode_jwt_token(token)

    # Extract user ID and role from token
    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id", "unknown")
    role = extract_role_from_token(payload)

    return User(user_id=user_id, role=role)


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to require admin role.

    Use this for endpoints that require admin privileges.

    Args:
        current_user: Current authenticated user (from get_current_user)

    Returns:
        User object (guaranteed to be admin)

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail="Admin access required. This operation requires admin privileges.",
        )
    return current_user


async def require_read_only_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that allows both read-only and admin users.

    This is the default for most endpoints. Use require_admin() for admin-only endpoints.

    Args:
        current_user: Current authenticated user

    Returns:
        User object
    """
    return current_user

