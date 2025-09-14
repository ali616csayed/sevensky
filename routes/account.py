from typing import Dict, Optional

from atproto import Client
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])

# In-memory session storage (use proper session management in production)
active_sessions: Dict[str, Client] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class AuthResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    user_info: Optional[dict] = None


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login with ATProtocol credentials
    """
    try:
        # Create new client for this user
        client = Client()

        # Attempt to login with ATProtocol
        profile = client.login(request.username, request.password)

        # Generate session ID (simple implementation - use proper session management in production)
        session_id = f"session_{len(active_sessions)}_{request.username}"

        # Store client in active sessions
        active_sessions[session_id] = client

        # Get user profile information
        user_info = {
            "did": profile.did,
            "handle": profile.handle,
            "display_name": getattr(profile, "display_name", ""),
            "description": getattr(profile, "description", ""),
        }

        return AuthResponse(
            success=True,
            message="Login successful",
            session_id=session_id,
            user_info=user_info,
        )

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {str(e)}")


@router.post("/logout", response_model=AuthResponse)
async def logout(session_id: str):
    """
    Logout and invalidate session
    """
    try:
        if session_id in active_sessions:
            # Remove client from active sessions
            del active_sessions[session_id]

            return AuthResponse(success=True, message="Logout successful")
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest):
    """
    Sign up for ATProtocol account (Note: ATProtocol signup requires invitation or specific server)
    This is a placeholder - actual signup would need to be handled by ATProtocol servers
    """
    try:
        # ATProtocol account creation is typically handled by the server
        # This is a simplified implementation that assumes the account already exists
        # and we're just verifying credentials

        client = Client()

        # Try to login with the provided credentials to verify account exists
        try:
            profile = client.login(request.username, request.password)

            # If login succeeds, the account exists and credentials are valid
            session_id = f"session_{len(active_sessions)}_{request.username}"
            active_sessions[session_id] = client

            user_info = {
                "did": profile.did,
                "handle": profile.handle,
                "display_name": getattr(profile, "display_name", ""),
                "description": getattr(profile, "description", ""),
            }

            return AuthResponse(
                success=True,
                message="Account verified and logged in",
                session_id=session_id,
                user_info=user_info,
            )

        except Exception:
            # If login fails, account doesn't exist or credentials are wrong
            raise HTTPException(
                status_code=400,
                detail="Account creation requires invitation or valid ATProtocol server. Please create an account through official ATProtocol clients first.",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.get("/profile")
async def get_profile(session_id: str):
    """
    Get current user profile information
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        client = active_sessions[session_id]

        # Get current user profile
        profile = client.me

        user_info = {
            "did": profile.did,
            "handle": profile.handle,
            "display_name": getattr(profile, "display_name", ""),
            "description": getattr(profile, "description", ""),
        }

        return {"success": True, "user_info": user_info}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.get("/sessions")
async def list_active_sessions():
    """
    List active sessions (for debugging - remove in production)
    """
    return {
        "active_sessions": len(active_sessions),
        "session_ids": list(active_sessions.keys()),
    }


def get_client_by_session(session_id: str) -> Client:
    """
    Helper function to get client by session ID
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return active_sessions[session_id]
