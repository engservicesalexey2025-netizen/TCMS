import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.enums import AuditAction


def log_action(
    db: Session,
    *,
    table_name: str,
    record_id: uuid.UUID,
    action: AuditAction,
    user_id: uuid.UUID | None,
    field_name: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    ip_address: str | None = None,
) -> None:
    db.add(
        AuditLog(
            TableName=table_name,
            RecordId=record_id,
            Action=action,
            ChangedByUserId=user_id,
            FieldName=field_name,
            OldValue=old_value,
            NewValue=new_value,
            IpAddress=ip_address,
        )
    )
