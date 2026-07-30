# Развёртывание TCMS на бесплатном хостинге

Инструкция по передаче TCMS реальным пользователям с использованием
полностью бесплатного стека. Рассчитана на низкую нагрузку (внутренний
корпоративный инструмент), не на публичный интернет-масштаб.

Итоговая архитектура — **$0/месяц**:

| Слой | Сервис |
|---|---|
| Backend | Render.com, бесплатный Web Service (Docker) |
| База данных | Neon, бесплатный serverless Postgres |
| Frontend | Cloudflare Pages, бесплатный статический хостинг |
| Файлы (аттестаты/документы) | Cloudflare R2, бесплатное S3-совместимое хранилище |

Единственный компромисс: бэкенд на бесплатном Render засыпает после 15 минут
простоя, первый запрос после этого грузится 30–60 секунд.

Шаги 1–4 требуют создания аккаунтов на внешних сервисах — это должен сделать
владелец проекта лично (агент не может создавать аккаунты за вас).

## 1. GitHub

1. Создайте пустой репозиторий на [github.com](https://github.com/new) (без
   README/gitignore/license — они уже есть локально).
2. В корне проекта:
   ```bash
   git remote add origin <URL вашего репозитория>
   git push -u origin master
   ```

Это станет источником авто-деплоя backend (Render) и frontend (Cloudflare
Pages) при каждом `git push`.

## 2. Neon — база данных

1. Зарегистрируйтесь на [neon.tech](https://neon.tech), создайте бесплатный проект.
2. Скопируйте **pooled connection string** — вид:
   `postgresql://user:password@host/dbname?sslmode=require`.
3. Приведите к формату, который ожидает `DATABASE_URL` (драйвер psycopg v3):
   ```
   postgresql+psycopg://user:password@host/dbname?sslmode=require
   ```
   Сохраните — понадобится на шаге 4.

## 3. Cloudflare R2 — хранилище файлов

1. Зарегистрируйтесь на [Cloudflare](https://dash.cloudflare.com) (если
   аккаунта ещё нет), откройте раздел **R2**.
2. Создайте бакет (например, `tcms-storage`).
3. В настройках бакета создайте **API-токен** (S3-совместимые ключи) — вы
   получите `Access Key ID` и `Secret Access Key`, а endpoint будет вида
   `https://<account-id>.r2.cloudflarestorage.com`.
4. Сохраните все 4 значения — понадобятся на шаге 4:
   `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`,
   `S3_BUCKET_NAME`.

## 4. Render — backend

1. Зарегистрируйтесь на [render.com](https://render.com), нажмите **New →
   Web Service**, подключите ваш GitHub-репозиторий.
2. Environment: **Docker**, Root Directory: `backend`.
3. Переменные окружения (Environment → Add Environment Variable):

   | Переменная | Значение |
   |---|---|
   | `DATABASE_URL` | строка из шага 2 |
   | `SECRET_KEY` | новый случайный ключ — сгенерировать: `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `CORS_ORIGINS` | `["https://ваш-домен.pages.dev"]` (заполните после шага 5, пока можно оставить `["http://localhost:5173"]`) |
   | `S3_ENDPOINT_URL` | из шага 3 |
   | `S3_ACCESS_KEY_ID` | из шага 3 |
   | `S3_SECRET_ACCESS_KEY` | из шага 3 |
   | `S3_BUCKET_NAME` | из шага 3 |
   | `SEED_ADMIN_LOGIN` | ваш логин администратора |
   | `SEED_ADMIN_EMAIL` | ваш email |
   | `SEED_ADMIN_PASSWORD` | новый надёжный пароль — **не** `ChangeMe123!` |

4. В настройках сервиса задайте команду запуска контейнера (Docker Command),
   заменив стандартный `CMD` из `Dockerfile` — на бесплатном плане Render
   нет отдельного «Pre-Deploy Command», поэтому миграции и сид выполняются
   прямо перед стартом сервера при каждом деплое:
   ```
   sh -c "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   ```
   `app/seed.py` безопасно перезапускать многократно — он не создаёт
   дубликаты, если роли/админ уже существуют.
5. Включите авто-деплой при push в основную ветку (обычно включено по
   умолчанию при подключении через GitHub).
6. После первого успешного деплоя скопируйте публичный URL сервиса (вида
   `https://tcms-backend.onrender.com`) — понадобится на шаге 5.

## 5. Cloudflare Pages — frontend

1. В Cloudflare Dashboard: **Workers & Pages → Create → Pages → Connect to
   Git**, выберите тот же репозиторий.
2. Root directory: `frontend`, build command: `npm run build`, output
   directory: `dist`.
3. Build-time переменная окружения (это переменная **времени сборки** — Vite
   «запекает» её в статический бандл, не рантайм-переменная):
   ```
   VITE_API_BASE_URL=https://<адрес-backend-на-render>/api/v1
   ```
4. После деплоя скопируйте публичный домен (вида `https://tcms.pages.dev`) и
   обновите `CORS_ORIGINS` на Render (шаг 4.3), указав точный адрес.

## 6. Финальная проверка

- `https://<backend>.onrender.com/health` отвечает `{"status": "ok"}`.
- Вход под администратором (логин/пароль из шага 4.3) через развёрнутый
  фронтенд.
- Загрузите тестовый PDF-аттестат, сделайте тривиальный передеплой backend
  (push пустого коммита), скачайте тот же файл повторно — подтверждение, что
  R2 сохраняет файлы между передеплоями.
- Пройдитесь по основным разделам (Сотрудники/Проекты/KPI/Заявки на доступ)
  под реальным админом.
