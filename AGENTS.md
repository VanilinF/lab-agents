# AGENTS.md

## О проекте
Лабораторная работа по ИИ-агентам: настройка opencode, MCP, skills.
Далее — веб-приложение для подготовки к экзамену (Django + PostgreSQL + Docker Compose).

## Стек
- Python 3.12, Django 5
- PostgreSQL 16
- Docker, Docker Compose

## Правила для агента
- Всегда отвечай на русском языке
- Перед изменением файлов кратко опиши план
- Код Python — PEP 8, type hints
- Секреты только в .env, никогда не коммить их
- Для документации по библиотекам используй MCP context7
- Отчёты оформляй через skill lab-report

## Структура
- docs/reports/ — отчёты по лабораторным
- .opencode/skills/ — skills агента

## Веб-приложение (папка web/)
- Django 5, PostgreSQL 16, запуск только через `docker compose`
- Все настройки (SECRET_KEY, DEBUG, параметры БД) — из переменных окружения, шаблон в `web/.env.example`
- Каждое изменение моделей сопровождается миграцией
- Для новых фич писать тесты (`python manage.py test`)
- Документацию Django/PostgreSQL проверять через MCP context7
- Не делать git commit самостоятельно — коммитит пользователь после ревью
