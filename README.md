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

## Структура
.
├── opencode.json                  # конфиг opencode + MCP (context7, filesystem)
├── AGENTS.md                      # правила для агента
├── .opencode/skills/lab-report/   # собственный skill
└── docs/reports/                  # отчёты и скриншоты

## Отчёты
- [На «3»: агент + MCP + Skill + AGENTS.md](docs/reports/lab-1.md)
