"""
Firebase Authentication Utilities
Provides token verification and protected endpoint decorators
"""

from fastapi import HTTPException, Depends, Header
from typing import Optional
import firebase_admin
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

async def verify_firebase_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify Firebase ID token from Authorization header.
    
    Expected header format: Authorization: Bearer <id_token>
    
    Returns:
        dict: Decoded token with user claims (uid, email, etc.)
        
    Raises:
        HTTPException: 401 if token is missing or invalid
                       403 if token is expired or malformed
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = parts[1]
    
    try:
        # Verify token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        logger.info(f"Token verified for user: {decoded_token.get('uid')}")
        return decoded_token
    except auth.InvalidIdTokenError as e:
        logger.warning(f"Invalid ID token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or malformed token"
        )
    except auth.ExpiredIdTokenError as e:
        logger.warning(f"Expired ID token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token expired. Please log in again"
        )
    except auth.RevokedIdTokenError as e:
        logger.warning(f"Revoked ID token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Token revoked. Please log in again"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=403,
            detail="Token verification failed"
        )


async def verify_optional_token(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Optionally verify Firebase ID token (for endpoints that support both auth and no-auth).
    
    Returns:
        dict or None: Decoded token if provided, None otherwise
    """
    if not authorization:
        return None
    
    try:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return auth.verify_id_token(parts[1])
    except Exception as e:
        logger.debug(f"Optional token verification failed: {e}")
    
    return None
