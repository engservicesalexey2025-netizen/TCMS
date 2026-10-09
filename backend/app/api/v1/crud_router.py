import uuid
from typing import Annotated, Callable, Type

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import DbSession, require_permission
from app.models.user import User
from app.schemas.common import Page
from app.services.crud_base import AuditedRepository


def build_crud_router(
    *,
    model: Type,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    out_schema: Type[BaseModel],
    prefix: str,
    tags: list[str],
    module: str,
    search_fields: list[str] | None = None,
    scoped: bool = False,
    validate_create: Callable[[Session, dict], None] | None = None,
    validate_update: Callable[[Session, object, dict], None] | None = None,
) -> APIRouter:
    """Собирает стандартный REST-эндпойнт (список/карточка/создание/
    правка/архив/восстановление) для одной сущности через универсальный
    репозиторий — новая справочная сущность подключается конфигурацией,
    без нового кода (Тома 1А §20).

    `module` — право (Permissions/RolePermissions, §13 ТЗ), которым
    гейтится каждое действие (VIEW/CREATE/UPDATE/DELETE). `scoped=True`
    включает Row-Level Security (§15 ТЗ) там, где модель описана в
    data_scope.SCOPE_RULES.

    `validate_create`/`validate_update` — опциональные хуки для бизнес-правил,
    которые не выразить общей CRUD-схемой (например, допустимая вложенность
    типов в самоссылающемся дереве OrgUnit) — бросают HTTPException при
    нарушении. `validate_update` получает уже загруженный текущий объект
    (до применения изменений), чтобы можно было проверить эффективное
    состояние с учётом полей, не пришедших в PATCH.
    """

    repo: AuditedRepository = AuditedRepository(model, search_fields=search_fields)
    router = APIRouter(prefix=prefix, tags=tags)

    ViewUser = Annotated[User, Depends(require_permission(module, "VIEW"))]
    CreateUser = Annotated[User, Depends(require_permission(module, "CREATE"))]
    UpdateUser = Annotated[User, Depends(require_permission(module, "UPDATE"))]
    DeleteUser = Annotated[User, Depends(require_permission(module, "DELETE"))]

    @router.get("", response_model=Page[out_schema])
    def list_items(
        db: DbSession,
        user: ViewUser,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        include_archived: bool = False,
    ):
        items, total = repo.list(
            db,
            skip=skip,
            limit=limit,
            search=search,
            include_archived=include_archived,
            user=user if scoped else None,
        )
        return Page(items=items, total=total, skip=skip, limit=limit)

    @router.get("/{item_id}", response_model=out_schema)
    def get_item(item_id: uuid.UUID, db: DbSession, user: ViewUser):
        obj = repo.get(db, item_id, user=user if scoped else None)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        return obj

    @router.post("", response_model=out_schema, status_code=status.HTTP_201_CREATED)
    def create_item(data: create_schema, db: DbSession, user: CreateUser):
        payload = data.model_dump()
        if validate_create:
            validate_create(db, payload)
        return repo.create(db, payload, user.Id)

    @router.patch("/{item_id}", response_model=out_schema)
    def update_item(
        item_id: uuid.UUID, data: update_schema, db: DbSession, user: UpdateUser
    ):
        obj = repo.get(db, item_id, user=user if scoped else None)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        payload = data.model_dump(exclude_unset=True)
        if validate_update:
            validate_update(db, obj, payload)
        obj = repo.update(db, item_id, payload, user.Id)
        return obj

    @router.post("/{item_id}/archive", response_model=out_schema)
    def archive_item(item_id: uuid.UUID, db: DbSession, user: DeleteUser):
        obj = repo.get(db, item_id, user=user if scoped else None)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        obj = repo.archive(db, item_id, user.Id)
        return obj

    @router.post("/{item_id}/restore", response_model=out_schema)
    def restore_item(item_id: uuid.UUID, db: DbSession, user: DeleteUser):
        obj = repo.get(db, item_id, user=user if scoped else None)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        obj = repo.restore(db, item_id, user.Id)
        return obj

    return router
