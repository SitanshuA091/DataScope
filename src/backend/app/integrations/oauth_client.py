from __future__ import annotations

from typing import Any, Mapping, TypedDict

from authlib.integrations.starlette_client import OAuth

from app.core.config import Settings


class GoogleUserInfo(TypedDict):
    google_sub: str
    email: str
    name: str | None
    avatar_url: str | None


def create_oauth_client(settings: Settings) -> OAuth:
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

    return oauth


def parse_google_user_info(user_info: Mapping[str, Any]) -> GoogleUserInfo:
    google_sub = str(user_info.get("sub") or "").strip()
    email = str(user_info.get("email") or "").strip().lower()

    if not google_sub or not email:
        raise ValueError("Google did not return the required account identity.")

    name = user_info.get("name")
    avatar_url = user_info.get("picture")

    return {
        "google_sub": google_sub,
        "email": email,
        "name": str(name).strip() if name else None,
        "avatar_url": str(avatar_url).strip() if avatar_url else None,
    }
