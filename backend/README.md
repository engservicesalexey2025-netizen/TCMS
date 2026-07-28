# TCMS Backend (FastAPI)

## Через Docker (из корня репозитория)

```bash
cp .env.example .env
docker compose up --build -d db backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Swagger: http://localhost:8000/docs

## Без Docker

Нужен доступный PostgreSQL (локальный или облачный) и его `DATABASE_URL`.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# .env в папке backend/, либо переменные окружения:
#   DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
#   SECRET_KEY=...

alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Первый вход

`python -m app.seed` создаёт 5 ролей (`Admin`, `DivisionDirector`,
`DepartmentHead`, `GroupHead`, `Observer`) и одного пользователя-администратора
(логин/пароль — см. `SEED_ADMIN_LOGIN` / `SEED_ADMIN_PASSWORD` в `.env`,
по умолчанию `admin` / `ChangeMe123!`). Все остальные пользователи заводятся
через `/api/v1/access-requests` → одобрение администратором.

## Миграции

```bash
alembic revision --autogenerate -m "описание изменения"
alembic upgrade head
```
