# Инструкция по сборке (основная)

**Один документ:** в каком порядке что собирать и какие команды запускать. Подробности — по ссылкам внизу.

---

## Что нужно заранее

- **Репозиторий:** клон ai_browser, submodule агента:  
  `git clone <репо> ai_browser && cd ai_browser && git submodule update --init packages/browseros-agent`
- **Chromium:** дерево исходников (~100 GB). Если ещё нет — [QUICKSTART.md](QUICKSTART.md): depot_tools, `fetch chromium`. Путь к исходникам — каталог **`src/`** (например `/path/to/chromium/src`).
- **Версия Chromium:** задаётся в `packages/browseros/CHROMIUM_VERSION` (тег в репо Chromium, например `145.0.7632.45`). При первой сборке с `--setup` скрипт сделает `checkout` этого тега и `gclient sync`.
- **Инструменты:** [Bun](https://bun.sh) 1.3.6 (агент), [UV](https://astral.sh/uv) (сборка браузера), для .crx — `pip install crx3` или npx.

---

## Порядок сборки (кратко)

| № | Что | Где | Команда / действие |
|---|-----|-----|---------------------|
| 1 | Расширение Agent (unpacked) | корень ai_browser | `./scripts/build_ponyai_extension.sh` |
| 2 | Бинарник browseros_server | корень ai_browser | `./scripts/build_browseros_server.sh` |
| 3 | Упаковать расширение в .crx | корень ai_browser | `./scripts/pack_agent_crx.sh` |
| 4 | Манифест для встройки | корень ai_browser | `python3 scripts/get_crx_extension_id.py packages/browseros/resources/extensions/agent-pack.crx --write-json` (если нет ключа agent.pem) |
| 5 | Браузер (Chromium + патчи + ресурсы) | packages/browseros | `uv sync` затем `uv run browseros build --chromium-src /path/to/chromium/src --setup --prep --build --build-type debug` |
| 6 | Запуск | — | `$CHROMIUM_SRC/out/Default_x64/browseros --user-data-dir=/tmp/test-profile` |

Команды 1–4 — из **корня** `ai_browser`. Команда 5 — из `packages/browseros`. Путь к Chromium подставь свой.

**Первый раз** обязательно с `--setup` (очистка дерева, checkout тега из CHROMIUM_VERSION, gclient sync). Дальше можно без `--setup`: только `--prep --build` или один `--build`.

---

## Копипаста (все шаги подряд)

Предполагается: репо с submodule, Bun, UV, Chromium уже получен. Подставь свой путь к `chromium/src`.

```bash
# 1. Расширение
./scripts/build_ponyai_extension.sh

# 2. Сервер
./scripts/build_browseros_server.sh

# 3. .crx
./scripts/pack_agent_crx.sh

# 4. Манифест (если упаковывали без ключа)
python3 scripts/get_crx_extension_id.py packages/browseros/resources/extensions/agent-pack.crx --write-json

# 5. Браузер (подставь свой CHROMIUM_SRC)
cd packages/browseros && uv sync && uv run browseros build --chromium-src /path/to/chromium/src --setup --prep --build --build-type debug 2>&1 | tee build.log

# 6. Запуск
# /path/to/chromium/src/out/Default_x64/browseros --user-data-dir=/tmp/test-profile
```

---

## R2 / облако не нужны для сборки

Шаг **download_resources** при сборке браузера не требует R2. Если переменные `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` не заданы — загрузка с R2 пропускается. Бинарник **browseros_server** нужно собрать локально (шаг 2) и положить в `packages/browseros/resources/binaries/browseros_server/` (скрипт шага 2 делает это сам).

---

## Дальше

- **Полная пошаговая инструкция с нюансами:** [docs/ponyai/build_all.md](ponyai/build_all.md)
- **Расширение:** версии, ключ .crx, bundled_extensions.json — [docs/ponyai/extension-build.md](ponyai/extension-build.md)
- **Chromium и первая сборка с нуля:** [QUICKSTART.md](QUICKSTART.md)
- **Подробно про сборку браузера и патчи:** [BUILD.md](BUILD.md)
