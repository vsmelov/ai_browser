# BrowserOS server — что мы собираем и где не путаться

## Кратко

**Мы собираем не «агента» (Chrome-расширение), а серверный бинарник `browseros_server`.**

- **BrowserOS-agent** — это репозиторий [browseros-ai/BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent). В нём три части:
  - **apps/server** — MCP/CDP-сервер (то, что мы собираем в бинарник `browseros_server`)
  - **apps/agent** — UI-расширение (чат, панель)
  - **apps/controller-ext** — расширение-мост для chrome.* API

- Когда мы запускаем `./scripts/build_browseros_server.sh`, мы собираем именно **сервер** (`apps/server`) в один исполняемый файл. Имя репо «BrowserOS-agent» общее для всего монорепо; для нашей сборки браузера нужен в первую очередь этот бинарник.

## Где что лежит

| Что | Где |
|-----|-----|
| Скрипт сборки сервера | `scripts/build_browseros_server.sh` |
| Готовый бинарник (после сборки) | `packages/browseros/resources/binaries/browseros_server/browseros-server-<os>-<arch>` (напр. `browseros-server-linux-x64`) |
| Клон BrowserOS-agent (кэш) | `.cache/BrowserOS-agent/` |
| Конфиг сервера (.env) | `.cache/BrowserOS-agent/apps/server/.env.development` (создаётся из `.env.example` скриптом при первом запуске) |

## Как собрать сервер

Из корня репозитория (нужны **git** и **Bun**):

```bash
./scripts/build_browseros_server.sh
```

При первом запуске скрипт клонирует BrowserOS-agent в `.cache/BrowserOS-agent`, при отсутствии создаёт `apps/server/.env.development` из `.env.example`, собирает бинарник и копирует его в `packages/browseros/resources/binaries/browseros_server/`. Сборка браузера потом подхватывает этот файл при копировании ресурсов.

Другие таргеты: `TARGET=linux-arm64 ./scripts/build_browseros_server.sh`. Существующий клон: `BROWSEROS_AGENT_DIR=/path/to/BrowserOS-agent ./scripts/build_browseros_server.sh`.

## Напоминание

- **browseros_server** = процесс-сервер (MCP, CDP, порты 9100/9000/9300), запускается из Chromium.
- **Agent (расширение)** = отдельная часть, в этом репо её сборка скриптом не трогаем; при необходимости см. BrowserOS-agent и `packages/browseros-agent/` в основном репо BrowserOS.

Подробнее про R2, заглушку и ручную сборку — в [BUILD.md](BUILD.md#browseros-server-бинарник-и-r2).
