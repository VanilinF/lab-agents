# Лабораторная работа: ИИ-агенты

## Требования
- Linux 
- git, Node.js + npm
- opencode

## Установка
sudo pacman -S --needed git nodejs npm curl
curl -fsSL https://opencode.ai/install | bash
opencode auth login

## Запуск
git clone <url-репозитория>
cd lab-agents
opencode mcp list   # проверка MCP-серверов
opencode

## Веб-приложение (web/)

Django 5 + PostgreSQL 16, запуск только через Docker Compose.

Запуск с нуля:

```bash
cd web
cp .env.example .env        # секреты/параметры БД, при необходимости отредактируй
docker compose up --build -d
```

Стек: `db` (postgres:16) стартует первой и становится healthy, затем `web`
применяет миграции и поднимает `runserver` на http://localhost:8000.

Дальше:

```bash
docker compose exec web python manage.py seed_questions   # наполнение вопросами (идемпотентно)
docker compose exec web python manage.py createsuperuser  # админка на /admin/
docker compose run --rm web python manage.py test         # все тесты
```

Стоп/очистка:

```bash
docker compose down        # остановить (volume postgres_data сохраняется)
docker compose down -v     # остановить и удалить данные БД
```

Если `.env` отсутствует, compose упадёт с `env file ... not found` — всегда
копируй `.env.example` → `.env` перед `up`.

## Структура
.
├── opencode.json                  # конфиг opencode + MCP (context7, filesystem)
├── AGENTS.md                      # правила для агента
├── .opencode/skills/lab-report/   # собственный skill
├── docs/reports/                  # отчёты и скриншоты
└── web/                           # Django-приложение (docker compose, quiz, accounts)

## Отчёты
- [На «3»: агент + MCP + Skill + AGENTS.md](docs/reports/lab-1.md)
