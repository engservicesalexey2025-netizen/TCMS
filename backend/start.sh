#!/bin/sh
# Продакшн-старт для Render: поле "Docker Command" там не поддерживает
# кавычки/&&, поэтому цепочка команд вынесена в отдельный файл — Docker
# Command становится однословным ("sh start.sh"), без риска ломающегося
# разбора пробелов/кавычек.
set -e
alembic upgrade head
python -m app.seed
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
