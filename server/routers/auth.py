import os
import secrets

from server.settings import ALLOWED_ORIGINS

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.responses import RedirectResponse

load_dotenv()

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("AUTH_CLIENT_ID"),
    client_secret=os.getenv("AUTH_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def get_current_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user

def verify_csrf_and_origin(request: Request) -> None:
    # 1. Check Origin header
    origin = request.headers.get("origin")
    if not origin or origin not in ALLOWED_ORIGINS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing Origin header",
        )

    # 2. Compare X-CSRF-Token header against the token in the signed session
    session_csrf = request.session.get("csrf_token")
    header_csrf = request.headers.get("x-csrf-token")

    if not session_csrf or not header_csrf or not secrets.compare_digest(session_csrf, header_csrf):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing or invalid",
        )


async def require_websocket_user(websocket: WebSocket) -> None:
    origin = websocket.headers.get("origin")
    if not origin or origin not in ALLOWED_ORIGINS:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    if not websocket.session.get("user"):
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info or not user_info.get("email_verified"):
        raise HTTPException(status_code=400, detail="Unverified Google account")

    sub = os.getenv("GOOGLE_SUB")

    if not sub or (sub and user_info["sub"] != sub):
        raise HTTPException(status_code=403, detail="Account not authorized")

    # Store user identity and generate a random CSRF token in the signed cookie
    request.session["user"] = {
        "sub": user_info["sub"],
        "email": user_info["email"],
        "name": user_info.get("name"),
    }
    request.session["csrf_token"] = secrets.token_urlsafe(32)
    redirect = os.getenv("APP_DEV") if os.getenv("ENVIRONMENT") == "dev" else os.getenv("APP_PROD")
    return RedirectResponse(url=redirect)


@router.get("/me")
async def get_me(request: Request, user: dict = Depends(get_current_user)):
    return {
        "user": user,
        "csrf_token": request.session.get("csrf_token"),
    }


@router.post(
    "/logout",
    dependencies=[Depends(verify_csrf_and_origin), Depends(get_current_user)],
)
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}