# Сборка расширения Agent (PonyClaw)

Кратко: где что лежит, какой коммит агента берём, команды. Source map при сборке расширения отключать всегда (иначе сборка идёт бесконечно).

## Что делать дальше (порядок шагов)

1. **Собрать расширение** → в `packages/browseros/resources/extensions/agent-build/` (unpacked). Скрипт: `build_ponyai_extension.sh` (есть на ветке `struggle_after_rebranding`; на main его можно взять оттуда или собрать вручную из субмодуля).
2. **Упаковать в .crx** → `pack_agent_crx.sh`. Скрипт создаёт `agent-pack.crx`. Ключ `agent.pem` в `packages/browseros/resources/extensions/` даёт стабильный ID (в форке: `ijlpinlejblenhkmjpgbjglcjibmlenp`).
3. **Положить для сборки браузера** в `packages/browseros/resources/extensions/`: файл `bundled_extensions.json` и `.crx`. Версия в JSON (`external_version`) должна совпадать с версией в `manifest.json` внутри собранного расширения (см. ниже).
4. **Сборка браузера** с `--prep`: шаг `bundled_extensions` при наличии в `resources/extensions/` файлов `bundled_extensions.json` и `*.crx` копирует их в дерево Chromium (локальные расширения); иначе расширения скачиваются с CDN.

---

## Папки

| Что | Путь |
|-----|------|
| Исходники агента (репо) | `packages/browseros-agent/` — **git submodule** (основной источник); при отсутствии субмодуля скрипты клонируют в `.cache/BrowserOS-agent/` |
| Расширение (исходники) | `apps/agent/` внутри репо BrowserOS-agent |
| Собранное расширение (unpacked) | `packages/browseros/resources/extensions/agent-build/` |
| Упакованный .crx и манифест | `packages/browseros/resources/extensions/*.crx`, `bundled_extensions.json` |
| Иконки для ребренда | `packages/browseros/resources/icons/` (копируются в `apps/agent/public/icon/`) |

Сборка браузера при наличии в `resources/extensions/` файлов `bundled_extensions.json` и `*.crx` копирует их в сборку (см. `bundled_extensions.py`).

---

## Версия / коммит BrowserOS-agent

Сборка согласована с **git submodule**:

- **Субмодуль** `packages/browseros-agent` — основной источник: скрипты (`build_browseros_server.sh`, при наличии — `build_ponyai_extension.sh`) по умолчанию берут агента из субмодуля, если он инициализирован (`git submodule update --init packages/browseros-agent`). Коммит субмодуля задаётся родительским репо. Проверить: `git submodule status` или `git rev-parse packages/browseros-agent`.
- **Fallback** — если субмодуль не инициализирован, скрипты клонируют репо в `.cache/BrowserOS-agent/` (при следующих запусках — `git pull`).

Чтобы зафиксировать версию агента:

- Обновить субмодуль на нужный коммит:  
  `cd packages/browseros-agent && git fetch && git checkout <коммит-или-тег>`, затем в корне ai_browser закоммитить обновлённый указатель: `git add packages/browseros-agent && git commit -m "chore: pin browseros-agent to <коммит>"`.
- Либо использовать свой клон: `BROWSEROS_AGENT_DIR=/path/to/clone ./scripts/build_browseros_server.sh`.

После мержа **PR #364** (fix: typescript checks in ci) в BrowserOS-agent в репо встроена схема GraphQL: `apps/agent/schema/schema.graphql`. Codegen работает без внешнего URL и без `BUILD_AGENT_WITHOUT_CLOUD=1` — удобно для сборки расширения.

---

## Команды (ветка struggle_after_rebranding)

Из **корня репо** `ai_browser`:

**1. Собрать расширение**

```bash
# С облачным API/codegen (после PR 364 схема в репо — можно без BUILD_AGENT_WITHOUT_CLOUD)
./scripts/build_ponyai_extension.sh

# Без облака (заглушки вместо codegen, быстрее)
BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh
```

Результат: `packages/browseros/resources/extensions/agent-build/`.

**2. Source map — отключать всегда**

Без отключения сборка расширения идёт бесконечно (известная особенность). В скрипте `build_ponyai_extension.sh` шаг `patch_sourcemap_off` подменяет в `apps/agent/wxt.config.ts` значение `sourcemap: 'hidden'` → `sourcemap: false`. При ручной сборке из BrowserOS-agent в `apps/agent/wxt.config.ts` задай `sourcemap: false`.

**3. Упаковать в .crx**

```bash
./scripts/pack_agent_crx.sh
```

При наличии ключа `packages/browseros/resources/extensions/agent.pem` получится `bflpfmnmnokmjhmgnolecpppdbdophmk.crx` (стабильный ID для `bundled_extensions.json`).

**Ключ подписи (agent.pem):** один раз упакуй расширение в Chrome (`chrome://extensions` → Pack extension), сохрани выданный `.pem` как `packages/browseros/resources/extensions/agent.pem`. Дальше все сборки с этим ключом дают один и тот же extension ID — его и указывают в `bundled_extensions.json`.

**Ensure extension version:** в `bundled_extensions.json` для каждого расширения задаётся `external_version`. Она должна **совпадать** с полем `version` в `manifest.json` внутри упакованного .crx. Установщик расширений в браузере (Chromium-патч) записывает эту версию в префы; если не совпадает — возможны лишние обновления или сбои. После каждой пересборки расширения с новой версией в манифесте нужно обновить `external_version` в `bundled_extensions.json`. Пример формата:

```json
{
  "ijlpinlejblenhkmjpgbjglcjibmlenp": {
    "external_crx": "agent-pack.crx",
    "external_version": "0.0.52"
  }
}
```
(В форке используем наш ID и `agent-pack.crx`; см. `bundled_extensions.json.example`.)

**4. Локальные расширения в сборке браузера**

Положить в `packages/browseros/resources/extensions/`:

- `bundled_extensions.json` (образец: `bundled_extensions.json.example`; поле `external_version` должно совпадать с `version` в `agent-build/manifest.json`);
- файл(ы) `*.crx` (имя файла — как в `external_crx` в JSON).

Дальше: обычная сборка браузера с `--prep`; модуль `bundled_extensions` скопирует эти файлы в дерево Chromium.

**5. Запуск собранного браузера (Linux)**

```bash
<chromium-src>/out/Default_x64/browseros --enable-logging=stderr --user-data-dir=/tmp/test-profile
```

(Или `PonyClaw` / другое имя бинарника в зависимости от брендинга.)

---

## Отключение source map (обязательно)

Source map при сборке расширения нужно **всегда** отключать — иначе сборка идёт бесконечно.

- В **скрипте** `build_ponyai_extension.sh`: отключение делается автоматически в шаге `patch_sourcemap_off`.
- **Вручную** в репо BrowserOS-agent: в `apps/agent/wxt.config.ts` задать `sourcemap: false`.

---

## См. также

- Официальная дока: [Contributing to BrowserOS](https://docs.browseros.com/contributing) (Path 1: Agent — `bun run build:agent`, Load unpacked).
- В этом репо: `packages/browseros/resources/extensions/README.md`, ветка `struggle_after_rebranding` — скрипты `build_ponyai_extension.sh`, `pack_agent_crx.sh`, логика «локальные extensions» в `bundled_extensions.py`.
- PR #364 в BrowserOS-agent: в репо добавлена `apps/agent/schema/schema.graphql`, codegen и TypeScript-проверки в CI работают без внешней схемы.
