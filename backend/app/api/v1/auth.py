import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_permission
from app.core.config import settings
from app.core.security import (
    check_password_strength,
    create_access_token,
    decode_token_payload,
    generate_reset_token,
    generate_temporary_password,
    hash_password,
    hash_reset_token,
    verify_password,
)
from app.models.enums import AuditAction
from app.models.permission import Delegation
from app.models.security import LoginHistory, PasswordHistory, PasswordResetToken, UserSession
from app.models.user import Role, User
from app.schemas.auth import (
    AdminResetPasswordOut,
    ChangePasswordIn,
    DelegationCreateIn,
    DelegationOut,
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginHistoryOut,
    MeOut,
    MfaDisableIn,
    MfaEnableIn,
    MfaEnableOut,
    MfaSetupOut,
    MfaVerifyIn,
    ResetPasswordIn,
    RoleOut,
    SessionOut,
    Token,
    ViewAsIn,
    ViewAsOut,
)
from app.schemas.common import Page
from app.services.audit import log_action
from app.services.permissions import get_active_role_ids, get_permission_summary
from app.services.sessions import issue_session_token, record_login_attempt, revoke_other_sessions

router = APIRouter(prefix="/auth", tags=["auth"])

MFA_PENDING_TOKEN_MINUTES = 5


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


@router.post("/login", response_model=Token)
def login(
    db: DbSession, request: Request, form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    ip_address, user_agent = _client_ip(request), _user_agent(request)
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
    )

    user = db.scalar(select(User).where(User.Login == form_data.username))
    if user is None or not user.IsActive:
        record_login_attempt(
            db, login_attempted=form_data.username, user=None, success=False,
            reason="USER_NOT_FOUND", ip_address=ip_address, user_agent=user_agent,
        )
        raise unauthorized

    now = datetime.now(timezone.utc)
    if user.LockedUntil is not None and user.LockedUntil > now:
        record_login_attempt(
            db, login_attempted=form_data.username, user=user, success=False,
            reason="LOCKED", ip_address=ip_address, user_agent=user_agent,
        )
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Учётная запись временно заблокирована из-за неудачных попыток входа",
        )

    if not verify_password(form_data.password, user.HashedPassword):
        user.FailedLoginAttempts += 1
        if user.FailedLoginAttempts >= settings.LOGIN_LOCKOUT_THRESHOLD:
            user.LockedUntil = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        db.commit()
        record_login_attempt(
            db, login_attempted=form_data.username, user=user, success=False,
            reason="BAD_PASSWORD", ip_address=ip_address, user_agent=user_agent,
        )
        raise unauthorized

    user.FailedLoginAttempts = 0
    user.LockedUntil = None
    db.commit()

    if user.MfaEnabled:
        mfa_token = create_access_token(
            user.Id, expires_minutes=MFA_PENDING_TOKEN_MINUTES, mfa_pending=True
        )
        return Token(access_token=mfa_token, requires_mfa=True)

    user.LastLoginAt = now
    user.LastLoginIp = ip_address
    token = issue_session_token(db, user, ip_address=ip_address, user_agent=user_agent)
    record_login_attempt(
        db, login_attempted=form_data.username, user=user, success=True,
        reason=None, ip_address=ip_address, user_agent=user_agent,
    )
    return Token(access_token=token)


@router.post("/login/verify-mfa", response_model=Token)
def verify_mfa(db: DbSession, request: Request, data: MfaVerifyIn) -> Token:
    ip_address, user_agent = _client_ip(request), _user_agent(request)
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный код подтверждения")

    payload = decode_token_payload(data.MfaToken)
    if payload is None or not payload.get("mfa_pending"):
        raise unauthorized
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.IsActive or not user.MfaEnabled or not user.MfaSecret:
        raise unauthorized

    valid = pyotp.TOTP(user.MfaSecret).verify(data.Code, valid_window=1)
    if not valid:
        valid = _consume_recovery_code(user, data.Code)
        if valid:
            db.commit()

    if not valid:
        record_login_attempt(
            db, login_attempted=user.Login, user=user, success=False,
            reason="MFA_FAILED", ip_address=ip_address, user_agent=user_agent,
        )
        raise unauthorized

    now = datetime.now(timezone.utc)
    user.LastLoginAt = now
    user.LastLoginIp = ip_address
    token = issue_session_token(db, user, ip_address=ip_address, user_agent=user_agent)
    record_login_attempt(
        db, login_attempted=user.Login, user=user, success=True,
        reason=None, ip_address=ip_address, user_agent=user_agent,
    )
    return Token(access_token=token)


def _consume_recovery_code(user: User, code: str) -> bool:
    if not user.MfaRecoveryCodesHash:
        return False
    import bcrypt

    hashes = json.loads(user.MfaRecoveryCodesHash)
    for i, code_hash in enumerate(hashes):
        if bcrypt.checkpw(code.encode("utf-8"), code_hash.encode("utf-8")):
            hashes.pop(i)
            user.MfaRecoveryCodesHash = json.dumps(hashes)
            return True
    return False


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, user: CurrentUser) -> None:
    jti = getattr(user, "_current_jti", None)
    if jti is not None:
        session = db.get(UserSession, jti)
        if session is not None:
            session.RevokedAt = datetime.now(timezone.utc)
            db.commit()


@router.get("/me", response_model=MeOut)
def read_current_user(db: DbSession, user: CurrentUser) -> MeOut:
    role_ids = get_active_role_ids(db, user)
    roles = db.scalars(select(Role).where(Role.Id.in_(role_ids))).all() if role_ids else []
    view_as = None
    if getattr(user, "_is_view_as", False):
        actor = db.get(User, user._view_as_actor_id)
        if actor is not None:
            view_as = ViewAsOut(OriginalUserId=actor.Id, OriginalLogin=actor.Login)

    return MeOut(
        Id=user.Id,
        Login=user.Login,
        Email=user.Email,
        EmployeeId=user.EmployeeId,
        Roles=[RoleOut.model_validate(r) for r in roles],
        MustChangePassword=user.MustChangePassword,
        Is2FAEnabled=user.MfaEnabled,
        ViewAs=view_as,
        Permissions=get_permission_summary(db, user),
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(db: DbSession, user: CurrentUser, data: ChangePasswordIn) -> None:
    if not verify_password(data.CurrentPassword, user.HashedPassword):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Текущий пароль указан неверно")

    strength_error = check_password_strength(data.NewPassword)
    if strength_error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, strength_error)

    recent_hashes = db.scalars(
        select(PasswordHistory.HashedPassword)
        .where(PasswordHistory.UserId == user.Id)
        .order_by(PasswordHistory.CreatedDate.desc())
        .limit(settings.PASSWORD_HISTORY_LIMIT)
    ).all()
    for old_hash in [user.HashedPassword, *recent_hashes]:
        if verify_password(data.NewPassword, old_hash):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Пароль не должен совпадать с последними {settings.PASSWORD_HISTORY_LIMIT} использованными",
            )

    db.add(PasswordHistory(UserId=user.Id, HashedPassword=user.HashedPassword))
    user.HashedPassword = hash_password(data.NewPassword)
    user.PasswordChangedAt = datetime.now(timezone.utc)
    user.MustChangePassword = False
    log_action(
        db, table_name="Users", record_id=user.Id, action=AuditAction.UPDATE,
        user_id=user.Id, field_name="HashedPassword",
    )
    db.commit()
    revoke_other_sessions(db, user, keep_jti=getattr(user, "_current_jti", None))


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(db: DbSession, data: ForgotPasswordIn) -> ForgotPasswordOut:
    """Публичный эндпойнт — всегда отвечает одинаково, независимо от того,
    существует ли email, чтобы не раскрывать список зарегистрированных
    пользователей (§9 ТЗ). Реальная отправка письма не подключена (решение
    согласовано с заказчиком) — до подключения SMTP пользователь должен
    обратиться к администратору, который выдаёт новый временный пароль через
    POST /auth/admin-reset-password/{{user_id}}."""
    user = db.scalar(select(User).where(User.Email == data.Email))
    if user is not None and user.IsActive:
        raw_token, token_hash = generate_reset_token()
        db.add(
            PasswordResetToken(
                UserId=user.Id,
                TokenHash=token_hash,
                ExpiresAt=datetime.now(timezone.utc)
                + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_MINUTES),
            )
        )
        db.commit()
    return ForgotPasswordOut(
        Detail="Если такой email зарегистрирован в системе, обратитесь к администратору "
        "для получения нового пароля."
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(db: DbSession, data: ResetPasswordIn) -> None:
    token_hash = hash_reset_token(data.Token)
    reset_token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.TokenHash == token_hash)
    )
    now = datetime.now(timezone.utc)
    if (
        reset_token is None
        or reset_token.UsedAt is not None
        or reset_token.ExpiresAt <= now
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ссылка недействительна или устарела")

    strength_error = check_password_strength(data.NewPassword)
    if strength_error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, strength_error)

    user = db.get(User, reset_token.UserId)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ссылка недействительна или устарела")

    db.add(PasswordHistory(UserId=user.Id, HashedPassword=user.HashedPassword))
    user.HashedPassword = hash_password(data.NewPassword)
    user.PasswordChangedAt = now
    user.MustChangePassword = False
    reset_token.UsedAt = now
    log_action(
        db, table_name="Users", record_id=user.Id, action=AuditAction.UPDATE,
        user_id=user.Id, field_name="HashedPassword",
        reason="Восстановление пароля по ссылке",
    )
    db.commit()
    revoke_other_sessions(db, user, keep_jti=None)


@router.post("/admin-reset-password/{user_id}", response_model=AdminResetPasswordOut)
def admin_reset_password(
    user_id: uuid.UUID,
    db: DbSession,
    admin: Annotated[User, Depends(require_permission("USERS", "UPDATE"))],
) -> AdminResetPasswordOut:
    """Практический путь «Забыли пароль» на время, пока не подключён SMTP:
    администратор выдаёт временный пароль так же, как при одобрении заявки
    на доступ (access_requests.py)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    temp_password = generate_temporary_password()
    db.add(PasswordHistory(UserId=user.Id, HashedPassword=user.HashedPassword))
    user.HashedPassword = hash_password(temp_password)
    user.MustChangePassword = True
    user.PasswordChangedAt = datetime.now(timezone.utc)
    log_action(
        db, table_name="Users", record_id=user.Id, action=AuditAction.UPDATE,
        user_id=admin.Id, field_name="HashedPassword",
        reason="Сброс пароля администратором",
    )
    db.commit()
    revoke_other_sessions(db, user, keep_jti=None)
    return AdminResetPasswordOut(TemporaryPassword=temp_password)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: DbSession, user: CurrentUser) -> list[SessionOut]:
    now = datetime.now(timezone.utc)
    current_jti = getattr(user, "_current_jti", None)
    rows = db.scalars(
        select(UserSession)
        .where(
            UserSession.UserId == user.Id,
            UserSession.RevokedAt.is_(None),
            UserSession.ExpiresAt > now,
        )
        .order_by(UserSession.IssuedAt.desc())
    ).all()
    return [
        SessionOut.model_validate(row).model_copy(
            update={"IsCurrent": row.Id == current_jti}
        )
        for row in rows
    ]


@router.post("/sessions/{session_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(session_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    session = db.get(UserSession, session_id)
    if session is None or session.UserId != user.Id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сессия не найдена")
    session.RevokedAt = datetime.now(timezone.utc)
    db.commit()


@router.get("/login-history", response_model=Page[LoginHistoryOut])
def login_history(
    db: DbSession, user: CurrentUser, skip: int = 0, limit: int = 50
) -> Page:
    query = select(LoginHistory).where(LoginHistory.UserId == user.Id).order_by(
        LoginHistory.CreatedDate.desc()
    )
    total = len(db.scalars(query).all())
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    return Page(
        items=[LoginHistoryOut.model_validate(r) for r in rows],
        total=total, skip=skip, limit=limit,
    )


@router.post("/mfa/setup", response_model=MfaSetupOut)
def mfa_setup(db: DbSession, user: CurrentUser) -> MfaSetupOut:
    secret = pyotp.random_base32()
    user.MfaSecret = secret
    db.commit()
    uri = pyotp.TOTP(secret).provisioning_uri(name=user.Email, issuer_name=settings.MFA_ISSUER_NAME)
    return MfaSetupOut(Secret=secret, ProvisioningUri=uri)


@router.post("/mfa/enable", response_model=MfaEnableOut)
def mfa_enable(db: DbSession, user: CurrentUser, data: MfaEnableIn) -> MfaEnableOut:
    import bcrypt

    if not user.MfaSecret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Сначала выполните /auth/mfa/setup")
    if not pyotp.TOTP(user.MfaSecret).verify(data.Code, valid_window=1):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неверный код подтверждения")

    recovery_codes = [uuid.uuid4().hex[:10] for _ in range(8)]
    hashes = [
        bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        for code in recovery_codes
    ]
    user.MfaEnabled = True
    user.MfaRecoveryCodesHash = json.dumps(hashes)
    log_action(
        db, table_name="Users", record_id=user.Id, action=AuditAction.UPDATE,
        user_id=user.Id, field_name="MfaEnabled", new_value="true",
    )
    db.commit()
    return MfaEnableOut(RecoveryCodes=recovery_codes)


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
def mfa_disable(db: DbSession, user: CurrentUser, data: MfaDisableIn) -> None:
    if not user.MfaEnabled or not user.MfaSecret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "2FA не включена")
    if not pyotp.TOTP(user.MfaSecret).verify(data.Code, valid_window=1) and not _consume_recovery_code(
        user, data.Code
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Неверный код подтверждения")

    user.MfaEnabled = False
    user.MfaSecret = None
    user.MfaRecoveryCodesHash = None
    log_action(
        db, table_name="Users", record_id=user.Id, action=AuditAction.UPDATE,
        user_id=user.Id, field_name="MfaEnabled", new_value="false",
    )
    db.commit()


@router.post("/view-as/{target_user_id}", response_model=Token)
def view_as(
    target_user_id: uuid.UUID,
    data: ViewAsIn,
    db: DbSession,
    request: Request,
    admin: Annotated[User, Depends(require_permission("USERS", "VIEW_AS"))],
) -> Token:
    """«Просмотреть как пользователь» (доп. рекомендация №4 ТЗ) — короткоживущий
    токен, строго read-only (см. require_permission в app/api/deps.py)."""
    target = db.get(User, target_user_id)
    if target is None or not target.IsActive:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")

    # sub = реально аутентифицированный admin (его и есть сессия/UserSessions
    # строка); acting_as = target — get_current_user() подставляет именно
    # его в качестве эффективного пользователя. Перепутать местами означало
    # бы, что "Просмотреть как" на деле возвращает права admin, а не target.
    token = issue_session_token(
        db, admin,
        ip_address=_client_ip(request), user_agent=_user_agent(request),
        acting_as=target.Id, expires_minutes=settings.VIEW_AS_TOKEN_MINUTES,
    )
    log_action(
        db, table_name="Users", record_id=target.Id, action=AuditAction.VIEW_AS,
        user_id=admin.Id, reason=data.Reason,
    )
    db.commit()
    return Token(access_token=token)


@router.get("/delegations", response_model=list[DelegationOut])
def list_delegations(db: DbSession, user: CurrentUser) -> list[DelegationOut]:
    """Исходящие делегирования текущего пользователя (доп. рекомендация №3
    ТЗ) — «Делегировать мой доступ» в личном кабинете."""
    now = datetime.now(timezone.utc)
    rows = db.scalars(
        select(Delegation).where(
            Delegation.FromUserId == user.Id,
            Delegation.IsActive.is_(True),
            Delegation.ExpiresAt > now,
        )
    ).all()
    out = []
    for d in rows:
        to_user = db.get(User, d.ToUserId)
        out.append(
            DelegationOut(
                Id=d.Id, FromUserId=d.FromUserId, ToUserId=d.ToUserId,
                ToUserLogin=to_user.Login if to_user else None,
                RoleId=d.RoleId, StartsAt=d.StartsAt, ExpiresAt=d.ExpiresAt, Reason=d.Reason,
            )
        )
    return out


@router.post("/delegations", response_model=DelegationOut, status_code=status.HTTP_201_CREATED)
def create_delegation(
    data: DelegationCreateIn,
    db: DbSession,
    user: Annotated[User, Depends(require_permission("DELEGATION", "CREATE"))],
) -> DelegationOut:
    target = db.get(User, data.ToUserId)
    if target is None or not target.IsActive:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    if target.Id == user.Id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Нельзя делегировать права самому себе")

    delegation = Delegation(
        FromUserId=user.Id, ToUserId=target.Id, RoleId=data.RoleId,
        StartsAt=datetime.now(timezone.utc), ExpiresAt=data.ExpiresAt, Reason=data.Reason,
        CreatedBy=user.Id, ModifiedBy=user.Id,
    )
    db.add(delegation)
    db.flush()
    log_action(
        db, table_name="Delegations", record_id=delegation.Id, action=AuditAction.CREATE,
        user_id=user.Id, reason=f"Делегировано пользователю {target.Login}",
    )
    db.commit()
    db.refresh(delegation)
    return DelegationOut(
        Id=delegation.Id, FromUserId=delegation.FromUserId, ToUserId=delegation.ToUserId,
        ToUserLogin=target.Login, RoleId=delegation.RoleId,
        StartsAt=delegation.StartsAt, ExpiresAt=delegation.ExpiresAt, Reason=delegation.Reason,
    )


@router.post("/delegations/{delegation_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_delegation(delegation_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    delegation = db.get(Delegation, delegation_id)
    if delegation is None or delegation.FromUserId != user.Id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Делегирование не найдено")
    delegation.IsActive = False
    delegation.ModifiedBy = user.Id
    db.commit()
