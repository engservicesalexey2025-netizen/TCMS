import uuid
from typing import Annotated, Type

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models.enums import RoleCode
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
    search_fields: list[str] | None = None,
    write_roles: tuple[RoleCode, ...] = (RoleCode.ADMIN,),
) -> APIRouter:
    """Собирает стандартный REST-эндпойнт (список/карточка/создание/
    правка/архив/восстановление) для одной сущности через универсальный
    репозиторий — новая справочная сущность подключается конфигурацией,
    без нового кода (Тома 1А §20).
    """

    repo: AuditedRepository = AuditedRepository(model, search_fields=search_fields)
    router = APIRouter(prefix=prefix, tags=tags)
    WriteUser = Annotated[User, Depends(require_roles(*write_roles))]

    @router.get("", response_model=Page[out_schema])
    def list_items(
        db: DbSession,
        _user: CurrentUser,
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
        )
        return Page(items=items, total=total, skip=skip, limit=limit)

    @router.get("/{item_id}", response_model=out_schema)
    def get_item(item_id: uuid.UUID, db: DbSession, _user: CurrentUser):
        obj = repo.get(db, item_id)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        return obj

    @router.post("", response_model=out_schema, status_code=status.HTTP_201_CREATED)
    def create_item(data: create_schema, db: DbSession, user: WriteUser):
        return repo.create(db, data.model_dump(), user.Id)

    @router.patch("/{item_id}", response_model=out_schema)
    def update_item(
        item_id: uuid.UUID, data: update_schema, db: DbSession, user: WriteUser
    ):
        obj = repo.update(db, item_id, data.model_dump(exclude_unset=True), user.Id)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        return obj

    @router.post("/{item_id}/archive", response_model=out_schema)
    def archive_item(item_id: uuid.UUID, db: DbSession, user: WriteUser):
        obj = repo.archive(db, item_id, user.Id)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        return obj

    @router.post("/{item_id}/restore", response_model=out_schema)
    def restore_item(item_id: uuid.UUID, db: DbSession, user: WriteUser):
        obj = repo.restore(db, item_id, user.Id)
        if obj is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Не найдено")
        return obj

    return router
