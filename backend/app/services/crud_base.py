import uuid
from typing import Generic, Type, TypeVar

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enums import AuditAction
from app.services.audit import log_action

ModelType = TypeVar("ModelType")


class AuditedRepository(Generic[ModelType]):
    """Universal entity repository: pagination, search, archive (soft
    delete), version bump and audit logging implemented once, so a new
    reference/entity table is wired up by configuration rather than bespoke
    CRUD code (Тома 1А §20 "Конструктор, а не программист"; §18 запрещает
    загружать всю таблицу — отсюда обязательные skip/limit).
    """

    def __init__(self, model: Type[ModelType], search_fields: list[str] | None = None):
        self.model = model
        self.table_name = model.__tablename__
        self.search_fields = search_fields or []

    def list(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
        include_archived: bool = False,
    ) -> tuple[list[ModelType], int]:
        query = select(self.model)
        if not include_archived:
            query = query.where(self.model.IsActive.is_(True))
        if search and self.search_fields:
            like = f"%{search}%"
            query = query.where(
                or_(*[getattr(self.model, f).ilike(like) for f in self.search_fields])
            )
        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = db.scalars(query.offset(skip).limit(limit)).all()
        return list(rows), total

    def get(self, db: Session, id: uuid.UUID) -> ModelType | None:
        return db.get(self.model, id)

    def create(self, db: Session, data: dict, user_id: uuid.UUID | None) -> ModelType:
        obj = self.model(**data, CreatedBy=user_id, ModifiedBy=user_id)
        db.add(obj)
        db.flush()
        log_action(
            db,
            table_name=self.table_name,
            record_id=obj.Id,
            action=AuditAction.CREATE,
            user_id=user_id,
        )
        db.commit()
        db.refresh(obj)
        return obj

    def diff_fields(self, obj: ModelType, data: dict) -> dict[str, tuple]:
        """Fields in `data` whose value differs from `obj`'s current value.

        Shared by update() (which writes the diff to AuditLog) and the
        import reconciliation preview (which only needs to *show* it) — so
        what a reviewer sees before confirming an import is guaranteed to
        match what update() would actually change.
        """
        return {
            field: (getattr(obj, field), new_value)
            for field, new_value in data.items()
            if getattr(obj, field) != new_value
        }

    def update(
        self, db: Session, id: uuid.UUID, data: dict, user_id: uuid.UUID | None
    ) -> ModelType | None:
        obj = self.get(db, id)
        if obj is None:
            return None
        for field, (old_value, new_value) in self.diff_fields(obj, data).items():
            log_action(
                db,
                table_name=self.table_name,
                record_id=obj.Id,
                action=AuditAction.UPDATE,
                user_id=user_id,
                field_name=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
            )
            setattr(obj, field, new_value)
        obj.ModifiedBy = user_id
        obj.Version += 1
        db.commit()
        db.refresh(obj)
        return obj

    def archive(self, db: Session, id: uuid.UUID, user_id: uuid.UUID | None) -> ModelType | None:
        obj = self.get(db, id)
        if obj is None:
            return None
        obj.IsActive = False
        obj.ModifiedBy = user_id
        obj.Version += 1
        log_action(
            db,
            table_name=self.table_name,
            record_id=obj.Id,
            action=AuditAction.ARCHIVE,
            user_id=user_id,
        )
        db.commit()
        db.refresh(obj)
        return obj

    def restore(self, db: Session, id: uuid.UUID, user_id: uuid.UUID | None) -> ModelType | None:
        obj = self.get(db, id)
        if obj is None:
            return None
        obj.IsActive = True
        obj.ModifiedBy = user_id
        obj.Version += 1
        log_action(
            db,
            table_name=self.table_name,
            record_id=obj.Id,
            action=AuditAction.RESTORE,
            user_id=user_id,
        )
        db.commit()
        db.refresh(obj)
        return obj
