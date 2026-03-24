# BuildCRM Starter

Теперь это не только API, но и простой локальный сайт для первого MVP.

## Что уже есть

- страница клиентов
- страница товаров
- страница заявок клиентов
- простая панель с количеством записей
- JSON API для клиентов, товаров и заявок
- поддержка SQLite для локальной разработки
- PostgreSQL можно подключить позже через `DATABASE_URL`

## Структура новых частей

```text
app/
├── api/routes/
│   ├── clients.py
│   ├── products.py
│   ├── requests.py
│   └── web.py
├── models/
│   ├── client.py
│   ├── product.py
│   └── client_request.py
├── services/
│   ├── client_service.py
│   ├── product_service.py
│   └── request_service.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── clients.html
│   ├── products.html
│   └── requests.html
└── static/
    └── styles.css
```

## Локальный запуск

### 1. Создай `.env`

Для локального запуска через SQLite:

```env
APP_NAME=BuildCRM
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./buildcrm.db
TG_BOT_TOKEN=
TG_TASK_CHAT_ID=0
```

### 2. Установи зависимости

```bash
pip install -r requirements.txt
```

### 3. Запусти проект

```bash
uvicorn app.main:app --reload
```

## Страницы

- `http://127.0.0.1:8000/dashboard`
- `http://127.0.0.1:8000/clients-page`
- `http://127.0.0.1:8000/products-page`
- `http://127.0.0.1:8000/requests-page`
- `http://127.0.0.1:8000/docs`

## Что лучше делать дальше

1. добавить редактирование и удаление
2. сделать нормальные миграции через Alembic
3. добавить авторизацию в веб-интерфейс
4. связать заявки и задачи
5. подключить Telegram-уведомления
