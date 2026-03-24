# BuildCRM Starter

Стартовый каркас для строительной CRM на **Python + FastAPI + PostgreSQL** с отдельным модулем **Telegram-бота**.

## Что внутри

- простой и понятный backend
- роли: `admin`, `director`, `manager`
- сущности: пользователи, клиенты, объекты/заказы, задачи, материалы, финансы
- Telegram-бот только для уведомлений и подтверждений задач
- Docker Compose для PostgreSQL

## Структура

```text
build-crm-starter/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── clients.py
│   │       ├── projects.py
│   │       ├── tasks.py
│   │       └── stats.py
│   ├── bot/
│   │   ├── handlers/
│   │   │   └── tasks.py
│   │   ├── keyboards/
│   │   │   └── task_actions.py
│   │   └── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   └── security.py
│   ├── models/
│   │   ├── base.py
│   │   ├── client.py
│   │   ├── finance.py
│   │   ├── material.py
│   │   ├── project.py
│   │   ├── task.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── client.py
│   │   ├── project.py
│   │   ├── task.py
│   │   └── user.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── notification_service.py
│   │   ├── stats_service.py
│   │   └── task_service.py
│   └── main.py
├── migrations/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Как запускать локально

### 1. Подними PostgreSQL

```bash
docker compose up -d
```

### 2. Создай виртуальное окружение и установи зависимости

```bash
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
pip install -r requirements.txt
```

### 3. Создай `.env`

```bash
cp .env.example .env
```

### 4. Запусти API

```bash
uvicorn app.main:app --reload
```

Документация FastAPI будет на:

- `http://127.0.0.1:8000/docs`

## Как запускать Telegram-бота

После заполнения `TG_BOT_TOKEN`:

```bash
python -m app.bot.main
```

## Логика ролей

### Admin
- управляет системой
- создаёт пользователей
- видит всё

### Director
- смотрит статистику, финансы, все проекты
- не обязательно редактирует всё подряд

### Manager
- ведёт клиентов
- создаёт объекты/заказы
- ставит задачи
- отслеживает выполнение

## Что делать первым этапом

1. Поднять проект и БД
2. Создать Alembic-миграции
3. Реализовать вход по JWT
4. Сделать CRUD для клиентов
5. Сделать CRUD для объектов/заказов
6. Сделать задачи и статусы
7. Подключить Telegram-уведомления
8. Добавить dashboard/статистику

## Рекомендуемый GitHub-процесс

### Первый пуш

```bash
git init
git branch -M main
git add .
git commit -m "Initial project structure"
git remote add origin git@github.com:YOUR_USERNAME/build-crm.git
git push -u origin main
```

### Ежедневная работа

```bash
git checkout -b feature/tasks-module
# работаешь с кодом
git add .
git commit -m "Add task service and task routes"
git push -u origin feature/tasks-module
```

После этого открываешь Pull Request на GitHub и вливаешь изменения в `main`.

### Полезные правила

- `main` — только стабильный код
- одна задача = одна ветка
- коммиты маленькие и понятные
- `.env` никогда не пушить
- перед пушем запускать проект локально

## Ближайшая хорошая цель

Сначала сделать только такой MVP:

- авторизация
- клиенты
- объекты/заказы
- задачи
- Telegram-уведомления по задачам

Без сложного склада, отчётов и бухгалтерии на первом этапе.
