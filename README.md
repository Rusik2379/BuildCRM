# BuildCRM Ready

Локальный MVP CRM для стройматериалов на FastAPI + SQLAlchemy + Jinja2.

## Что есть
- Розничные заявки
- Оптовые заявки
- Клиенты и карточка клиента
- Номенклатура
- Склад
- Поставщики и баланс
- Водители и деньги на руках
- Финансы
- Документы (заглушка-раздел)

## Запуск
```bash
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Открыть:
- http://127.0.0.1:8000/dashboard

## Тесты
```bash
pytest -q
```

## База данных
По умолчанию SQLite:
- `sqlite:///./buildcrm_ready.db`

Для изменения можно задать переменную окружения `DATABASE_URL`.


Важно: архив рассчитан на распаковку поверх старого проекта тоже; модели и сервисы теперь лежат в app/models/__init__.py и app/services/__init__.py, чтобы не конфликтовать с существующими папками.
