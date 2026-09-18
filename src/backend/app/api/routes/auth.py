## Google OAuth login, callback, logout, current user
from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.db.models.user import User
from app.schemas.auth import CurrentUserResponse
from app.services.auth_service import get_or_create_google_user


router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth = OAuth()

oauth.register(
    name="google",
    server_metadata_url=(
        "https://accounts.google.com/.well-known/openid-configuration"
    ),
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret.get_secret_value(),
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    return await oauth.google.authorize_redirect(
        request,
        settings.google_oauth_redirect_uri,
    )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if user_info is None:
            user_info = await oauth.google.parse_id_token(request, token)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google sign-in could not be completed.",
        ) from exc

    google_sub = user_info.get("sub")
    email = user_info.get("email")

    if not google_sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google did not return the required account identity.",
        )

    user = get_or_create_google_user(
        db=db,
        google_sub=google_sub,
        email=email,
        name=user_info.get("name"),
        avatar_url=user_info.get("picture"),
    )

    request.session.clear()
    request.session["user_id"] = str(user.id)

    return RedirectResponse(
        url=f"{settings.frontend_url.rstrip('/')}/workspaces",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=CurrentUserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
    )