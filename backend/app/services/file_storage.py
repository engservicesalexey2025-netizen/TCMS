"""Абстракция файлового хранилища для загружаемых вложений (аттестаты
сотрудников, документы проектов).

Если S3_BUCKET_NAME не задан — работа с локальным диском под
FILE_STORAGE_PATH (сегодняшнее поведение, без изменений для
docker-compose/локальной разработки). Если задан — работа через
S3-совместимый API (например, Cloudflare R2) через boto3, чтобы
загруженные файлы переживали передеплой на хостингах с эфемерным диском
(см. план развёртывания на бесплатном хостинге)."""
from pathlib import Path

from app.core.config import settings

STORAGE_ROOT = Path(settings.FILE_STORAGE_PATH).resolve()


def _use_s3() -> bool:
    return bool(settings.S3_BUCKET_NAME)


def _client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _safe_path(relative_path: str) -> Path:
    full = (STORAGE_ROOT / relative_path).resolve()
    if not full.is_relative_to(STORAGE_ROOT):
        raise ValueError("Недопустимый путь к файлу")
    return full


def save(relative_path: str, data: bytes) -> None:
    if _use_s3():
        _client().put_object(Bucket=settings.S3_BUCKET_NAME, Key=relative_path, Body=data)
        return
    full = _safe_path(relative_path)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(data)


def read(relative_path: str) -> bytes | None:
    if _use_s3():
        client = _client()
        try:
            obj = client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=relative_path)
        except client.exceptions.NoSuchKey:
            return None
        return obj["Body"].read()
    full = _safe_path(relative_path)
    if not full.is_file():
        return None
    return full.read_bytes()


def delete(relative_path: str) -> None:
    if _use_s3():
        _client().delete_object(Bucket=settings.S3_BUCKET_NAME, Key=relative_path)
        return
    full = _safe_path(relative_path)
    full.unlink(missing_ok=True)


def exists(relative_path: str) -> bool:
    if _use_s3():
        client = _client()
        try:
            client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=relative_path)
            return True
        except client.exceptions.ClientError:
            return False
    full = _safe_path(relative_path)
    return full.is_file()
