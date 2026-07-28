from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    db: DbSession, form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    user = db.scalar(select(User).where(User.Login == form_data.username))
    if (
        user is None
        or not user.IsActive
        or not verify_password(form_data.password, user.HashedPassword)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    return Token(access_token=create_access_token(user.Id))


@router.get("/me", response_model=UserOut)
def read_current_user(user: CurrentUser) -> UserOut:
    return UserOut(
        Id=user.Id,
        Login=user.Login,
        Email=user.Email,
        RoleCode=user.Role.Code,
        EmployeeId=user.EmployeeId,
    )
