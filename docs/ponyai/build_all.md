# Сборка всего: расширение, сервер, браузер

Пошаговая последовательность: расширение Agent (unpacked → .crx), бинарник browseros_server, сборка браузера с встроенным расширением и запуск. Новый разработчик может повторить всё по этому документу, если выполнены предварительные условия ниже.

---

## Для нового разработчика: с чего начать

1. **Клонировать репо и submodule:**  
   `git clone <репо> ai_browser && cd ai_browser && git submodule update --init packages/browseros-agent`

2. **Chromium:** если дерева Chromium ещё нет — сначала [QUICKSTART.md](../QUICKSTART.md): depot_tools, `fetch chromium` (~100 GB), проверка тега. Путь к исходникам — каталог `src/` (например `~/chromium/src` или `/home/ubuntu/knx-west/aib/chromium/src`). Без Chromium шаг 5 не выполнить.

3. **Инструменты:** Bun 1.3.6, UV (в `packages/browseros`), для упаковки .crx — npx или Python + crx3. См. раздел «Что нужно заранее» ниже.

4. **Все команды шагов 1–4** выполняются из **корня репо** `ai_browser`. Шаги 5–6 — из `packages/browseros` и с путём к Chromium.

---

## Что нужно заранее

- **Репозиторий:** клон ai_browser, submodule инициализирован: `git submodule update --init packages/browseros-agent`.
- **Bun 1.3.6** (как в engines у browseros-agent). Установка: `curl -fsSL https://bun.sh/install | bash -s bun-v1.3.6`. При странных ошибках сборки расширения: `bun pm cache rm --global`.
- **Chromium:** исходники по [QUICKSTART](../QUICKSTART.md) (depot_tools, `fetch chromium`). Путь к дереву — каталог `src/` (например `/home/ubuntu/knx-west/aib/chromium/src`).
- **UV** для сборки браузера: `cd packages/browseros && uv sync` (один раз или после обновления зависимостей).
- **Упаковка .crx:** Node.js (npx) или Python с пакетом **crx3** (`pip install crx3`). Без этого шаг 3 сделает только unpacked расширение; для встройки в браузер нужен .crx (шаги 3–4).

---

## Порядок шагов

Все команды ниже — из **корня репо** `ai_browser`, если не указано иное.

### 1. Собрать расширение (unpacked)

```bash
./scripts/build_ponyai_extension.sh
```

- Результат: `packages/browseros/resources/extensions/agent-build/`.
- Скрипт проверяет bun 1.3.6, при необходимости чисти кэш: `bun pm cache rm --global`.
- В submodule допускаются только изменения `apps/agent/lib/env.ts` (фикс zod под vite-node) и `bun.lock`.
zod fix discussion - https://discord.com/channels/1373640905223045141/1373641063557759007/1477597542479822981






### 2. Собрать browseros_server

```bash
./scripts/build_browseros_server.sh
```

- Результат: бинарник в `packages/browseros/resources/binaries/browseros_server/` (например `browseros-server-linux-x64`).
- Без него браузер соберётся, но MCP/CDP-сервер не будет работать.





### 3. Упаковать расширение в .crx

```bash
./scripts/pack_agent_crx.sh
```

- Если есть ключ `packages/browseros/resources/extensions/agent.pem` → создаётся `bflpfmnmnokmjhmgnolecpppdbdophmk.crx` (стабильный ID).
- Если ключа нет → создаётся `agent-pack.crx` и `agent-pack.pem`. Сохрани `.pem` как `agent.pem` для следующих раз:  
  `cp packages/browseros/resources/extensions/agent-pack.pem packages/browseros/resources/extensions/agent.pem`





### 4. Создать bundled_extensions.json (обязательно после упаковки без ключа)

Если получили `agent-pack.crx`, выполни **один раз** (из корня репо):

```bash
python3 scripts/get_crx_extension_id.py packages/browseros/resources/extensions/agent-pack.crx --write-json
```

Скрипт создаст `packages/browseros/resources/extensions/bundled_extensions.json` с нужным ID и версией. Файл `.crx` уже лежит там же. Без этого шага сборка браузера подхватит расширения с CDN, а не твой собранный пакет.

(Если упаковывали с ключом `agent.pem`, получится `bflpfmnmnokmjhmgnolecpppdbdophmk.crx` — тогда можно скопировать `bundled_extensions.json.example` в `bundled_extensions.json` и проверить, что `external_version` совпадает с версией в manifest.)





### 5. Собрать браузер

Подставь свой путь к дереву Chromium (где лежит `src/` после `fetch chromium`). Пример для типичной раскладки на этой машине. **Первый раз обязательно с `--setup`** (очистка дерева, checkout тега, gclient sync).

```bash
cd packages/browseros
uv sync
uv run browseros build --chromium-src /home/ubuntu/knx-west/aib/chromium/src --setup --prep --build --build-type debug 2>&1 | tee build.log
```

- Лог сборки сохранится в `packages/browseros/build.log`. Дальше можно запускать без `--setup` (только `--prep --build` или просто `--build`).
- Шаг `bundled_extensions` при наличии локальных `bundled_extensions.json` и `.crx` в `resources/extensions/` копирует их в дерево Chromium (расширение встроится в браузер).
- Путь к Chromium подставь свой (если не `/home/ubuntu/knx-west/aib/chromium/src`).





### 6. Запуск браузера (Linux debug)

```bash
/home/ubuntu/knx-west/aib/chromium/src/out/Default_x64/browseros --user-data-dir=/tmp/test-profile
```

(Путь к бинарнику — тот же каталог Chromium, что в `--chromium-src`, плюс `out/Default_x64/browseros`.)

---

## Краткий чеклист

| Шаг | Команда / действие |
|-----|---------------------|
| 1 | `./scripts/build_ponyai_extension.sh` |
| 2 | `./scripts/build_browseros_server.sh` |
| 3 | `./scripts/pack_agent_crx.sh` |
| 4 | `python3 scripts/get_crx_extension_id.py packages/browseros/resources/extensions/agent-pack.crx --write-json` (если получили agent-pack.crx) |
| 5 | `cd packages/browseros && uv sync && uv run browseros build --chromium-src /home/ubuntu/knx-west/aib/chromium/src --setup --prep --build --build-type debug 2>&1 \| tee build.log` |
| 6 | Запуск: `/home/ubuntu/knx-west/aib/chromium/src/out/Default_x64/browseros --user-data-dir=/tmp/test-profile` |

---

## Повторить всё по порядку (копипаста)

Предполагается: репо с submodule, Bun 1.3.6, Chromium уже получен (QUICKSTART), путь к нему известен. Команды 1–4 — из корня `ai_browser`, 5 — из `packages/browseros`.

```bash
# 1. Расширение (unpacked)
./scripts/build_ponyai_extension.sh

# 2. Сервер
./scripts/build_browseros_server.sh

# 3. Упаковать расширение в .crx
./scripts/pack_agent_crx.sh

# 4. Если получили agent-pack.crx — создать bundled_extensions.json
python3 scripts/get_crx_extension_id.py packages/browseros/resources/extensions/agent-pack.crx --write-json

# 5. Собрать браузер (подставь свой CHROMIUM_SRC при необходимости)
cd packages/browseros && uv sync && uv run browseros build --chromium-src /home/ubuntu/knx-west/aib/chromium/src --setup --prep --build --build-type debug 2>&1 | tee build.log

# 6. Запуск (тот же путь, что в --chromium-src)
/home/ubuntu/knx-west/aib/chromium/src/out/Default_x64/browseros --user-data-dir=/tmp/test-profile
```

---

## До-сборка: обновить сервер и расширение без полной перекомпиляции

Когда браузер уже собран и нужно только подставить **новый бинарник сервера** и/или **новый .crx расширения** (без пересборки всего Chrome):

Все команды 1–4 — из **корня репо** `ai_browser`, 5 — из `packages/browseros`. Подставь свой путь к Chromium вместо `/home/ubuntu/knx-west/aib/chromium/src`.

```bash
# 1. Сервер (с фиксом pino-pretty и проверкой logger)
./scripts/build_browseros_server.sh

# 2. Расширение (unpacked)
./scripts/build_ponyai_extension.sh

# 3. Упаковать в .crx
./scripts/pack_agent_crx.sh

# 4. Если упаковывали без ключа (получили agent-pack.crx) — один раз обновить ID в json
python3 scripts/get_crx_extension_id.py packages/browseros/resources/extensions/agent-pack.crx --write-json

# 5. Подставить ресурсы в дерево Chromium и пересобрать только то, что нужно (COPY + link, не полная перекомпиляция)
cd packages/browseros
uv run browseros build --chromium-src /home/ubuntu/knx-west/aib/chromium/src -m resources,bundled_extensions,compile --build-type debug
```

Шаг 5 копирует бинарник из `resources/binaries/browseros_server/` и расширения из `resources/extensions/` в дерево Chromium и запускает `autoninja`; ninja перезапустит только правила COPY и при необходимости финальную линковку, без полной перекомпиляции.

---

## См. также

- [QUICKSTART.md](../QUICKSTART.md) — репо, Chromium, первая сборка браузера.
- [extension-build.md](extension-build.md) — детали по расширению, версиям, ключу.
- [BUILD.md](../BUILD.md) — полное описание сборки браузера.
