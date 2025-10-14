# 🚀 Crypto Portfolio & Alerts API (FastAPI)

> Pet-проект для демонстрации навыков Python, FastAPI, интеграции с внешними API, БД, Redis и построения продвинутой серверной логики.
> ✅ Все основные функции реализованы, можно разворачивать локально или на Railway.

---

## 🧰 Технологии
- 🐍 Python 3.12 + FastAPI
- 🐘 PostgreSQL + SQLAlchemy + Alembic
- 🧠 Redis Cloud (кэш цен и rate-limit)
- 🪙 CoinGecko API (цены криптовалют)
- 🛰 APScheduler (периодические задачи)
- 🧪 Pytest

---

## ✨ Основной функционал
- 🔐 JWT-авторизация (регистрация и вход)
- 📊 CRUD для портфелей и позиций
- 💰 `/prices` — получение актуальных цен через CoinGecko (кэш в Redis)
- 📈 `/portfolio/{id}/summary` — общая стоимость и PnL
- ⚡ Алерты по цене с антиспам-механизмом (cooldown)
- 🧯 Rate limit на публичные ручки (реализован через Redis ZSET — скользящее окно)
- 📡 `/health/status` — проверка доступности БД, Redis, CoinGecko и Telegram конфигурации
- 🛰 Ретраи при сбоях сетевых запросов (CoinGecko, Telegram)

---

## 🧭 Архитектура
```mermaid
flowchart LR
  Client <--> FastAPI
  subgraph API
    routers[(Routers: auth, prices, portfolio, positions, alerts)]
    services[Services: pricing, coingecko, alerts, notifier]
    scheduler[APScheduler job]
  end
  DB[(PostgreSQL)] --- API
  Redis[(Redis Cloud)] --- API
  CoinGecko[(CoinGecko API)] --- services
  Telegram[(Telegram Bot API)] --- services
```

---

## ⚙️ Установка и запуск (локально)

1. Клонируй репозиторий:
   ```bash
   git clone <your-repo-url>
   cd <project-folder>
   ```

2. Установи зависимости:
   ```bash
   python -m venv venv
   source venv/bin/activate   # или venv\Scripts\activate на Windows
   pip install -r requirements.txt
   ```

3. Укажи переменные окружения в `.env`:
   ```env
   DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/yourdb
   REDIS_URL=rediss://default:<PASSWORD>@<HOST>:6380/0
   JWT_SECRET=your_secret
   DEFAULT_VS=usd
   ALERT_COOLDOWN_SEC=60
   ```

4. Примените миграции:
   ```bash
   alembic upgrade head
   ```

5. Запусти сервер:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🚂 Запуск на Ra

1. 📦 Задеплой репозиторий на Railway (Deploy from GitHub).
2. Подключи **PostgreSQL** (плагин) → скопируй `DATABASE_URL`.
3. Подключи **Redis Cloud** (или аналог) → задай `REDIS_URL` вида:
   ```
   rediss://default:PASSWORD@HOST:6380/0
   ```
4. Добавь в переменные окружения:
   ```
   JWT_SECRET=your_secret
   DEFAULT_VS=usd
   ALERT_COOLDOWN_SEC=60
   ```
   *(опционально)* `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

5. В Railway **Run Command** выполни:
   ```bash
   alembic upgrade head
   python -m app.services.seed_demo
   ```
   Это создаст демо-юзера и тестовые данные.

6. Готово! Перейди по Railway URL → `/docs` и протестируй API.

---

## 🧪 Тесты и линтинг
```bash
pytest -q         # тесты
```

---

## 📡 Основные эндпоинты

| Метод | URL                        | Назначение                                  |
|-------|-----------------------------|---------------------------------------------|
| POST  | `/auth/signup`              | Регистрация                                 |
| POST  | `/auth/login`               | JWT-авторизация                             |
| GET   | `/prices`                   | Получить цены                              |
| GET   | `/portfolio/{id}/summary`   | PnL и стоимость портфеля                   |
| POST  | `/alerts`                   | Создать алерт                              |
| GET   | `/health/status`           | Проверка статуса систем                    |

---

## 👤 Демо-юзер (после сидов)
```
email: demo@user.io
password: demo1234
```

---

## 📄 Лицензия
MIT License — можно использовать как базу для собственных pet-проектов.
