import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials

from .config import settings

reusable_oauth2 = HTTPBearer()


# Initialize Firebase Admin SDK
# This must be done only once when the application starts.
def initialize_firebase_app():
    """
    Initialize the Firebase Admin SDK using the credentials from the settings.
    """
    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase App initialized successfully.")
    except Exception as e:
        # This is a critical failure, the app should not start without it.
        print(f"FATAL: Could not initialize Firebase Admin SDK: {e}")
        raise


# Authentication Dependency
async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
) -> dict:
    """
    A FastAPI dependency that verifies the Firebase ID token.

    Args:
        creds: The HTTP Authorization credentials extracted by HTTPBearer.

    Returns:
        The decoded token as a dictionary, which includes user info like uid, email, etc.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid, expired, or not provided.
    """
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Firebase Admin SDK verifies the token.
        # It checks the signature, expiration, and audience.
        token = creds.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase ID token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # Catch any other potential errors during verification
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process authentication token",
        )
