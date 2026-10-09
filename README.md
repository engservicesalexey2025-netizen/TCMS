# TSMS — Technical Supervision Management System

Веб-система технического надзора за строительством. Концепция и стандарт
проектирования — см. `1 TCMS Анализ файлов системы.pdf` (Том 1, идеология) и
`1А TCMS Анализ файлов системы.pdf` (Том 1А, стандарт проектирования).

Стек: PostgreSQL, FastAPI + SQLAlchemy + Alembic, Vue 3 + Vite + PrimeVue, JWT-авторизация.

## Структура репозитория

```
backend/    FastAPI-приложение (API, бизнес-логика, модели, миграции)
frontend/   Vue 3 SPA
docker-compose.yml
```

## Быстрый старт (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000/docs (Swagger)
- Frontend: http://localhost:5173

## Быстрый старт без Docker

См. `backend/README.md` и `frontend/README.md` — там же инструкции, как
подключить локальный или облачный PostgreSQL через `DATABASE_URL`.

## Текущее состояние локального окружения (эта машина)

На этой машине нет Docker и нет системного PostgreSQL, поэтому используется
портативный PostgreSQL 18.4 (zip-дистрибутив EnterpriseDB, без инсталлятора)
в `.pgportable/` — эта папка в `.gitignore`, при клонировании репозитория её
не будет.

Запуск/остановка:

```bash
# из корня репозитория
.pgportable/pgsql/bin/pg_ctl.exe -D .pgportable/data -l .pgportable/logfile.txt -o "-p 5432" start
.pgportable/pgsql/bin/pg_ctl.exe -D .pgportable/data stop
```

БД `tcms`, пользователь `tcms`/`tcms` (см. `.env`). Бэкенд и фронтенд
запускаются через `.claude/launch.json` (backend: uvicorn на 8000,
frontend: vite на 5173).

Первый вход: логин `admin`, пароль `ChangeMe123!` (см. `SEED_ADMIN_PASSWORD`
в `.env`) — обязательно смените после первого входа, т.к. это dev-заглушка.

Driver: используется `psycopg` (v3), а не `psycopg2` — на момент настройки
для установленной версии Python не было готового бинарного пакета
`psycopg2-binary`.

## Роли системы

Иерархия доступа: `Admin → DivisionDirector → DepartmentHead → GroupHead → Observer`.
Наблюдатель может быть назначен на несколько организационных единиц
(связь многие-ко-многим через `UserOrgAccess`). Выдача роли происходит через
заявку на доступ (`AccessRequest`), которую одобряет Admin.
