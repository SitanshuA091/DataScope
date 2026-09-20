from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.user import User


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
        user.email = normalized_email
        user.name = name
        user.avatar_url = avatar_url

        db.commit()
        db.refresh(user)
        return user

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

        return existing_user

    db.refresh(user)
    return user