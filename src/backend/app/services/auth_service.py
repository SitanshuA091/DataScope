from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.user import User


def _update_google_user(
    user: User,
    *,
    email: str,
    name: str | None,
    avatar_url: str | None,
) -> User:
    user.email = email
    user.name = name
    user.avatar_url = avatar_url
    return user


def get_or_create_google_user(
    db: Session,
    google_sub: str,
    email: str,
    name: str | None,
    avatar_url: str | None,
) -> User:
    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.google_sub == google_sub)
    )

    if user is not None:
        _update_google_user(
            user,
            email=normalized_email,
            name=name,
            avatar_url=avatar_url,
        )

        db.commit()
        db.refresh(user)
        return user

    email_owner = db.scalar(select(User).where(User.email == normalized_email))

    if email_owner is not None:
        raise ValueError("A user already exists for this email address.")

    user = User(
        google_sub=google_sub,
        email=normalized_email,
        name=name,
        avatar_url=avatar_url,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        existing_user = db.scalar(
            select(User).where(User.google_sub == google_sub)
        )

        if existing_user is None:
            raise

        _update_google_user(
            existing_user,
            email=normalized_email,
            name=name,
            avatar_url=avatar_url,
        )
        db.commit()
        db.refresh(existing_user)
        return existing_user

    db.refresh(user)
    return user
