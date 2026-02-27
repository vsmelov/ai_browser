# Сборка расширения Agent с брендингом PonyAI

## Как получить браузер со встроенным расширением PonyAI (кратко)

Сделайте **четыре шага по порядку** (все команды — из корня репо `ai_browser`):

| Шаг | Что сделать |
|-----|-------------|
| **1** | Собрать расширение: `BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh` |
| **2** | Упаковать в .crx: `./scripts/pack_agent_crx.sh` |
| **3** | Положить в `packages/browseros/resources/extensions/`: файл **`bflpfmnmnokmjhmgnolecpppdbdophmk.crx`** (если скрипт его создал) или переименовать **`agent-pack.crx`** в **`<id>.crx`** (ID смотрите в Chrome после загрузки) и создать **`bundled_extensions.json`** (см. ниже). |
| **4** | Собрать браузер как обычно (например `./packages/browseros/build/cli/build.py --prep` и дальше сборка Chromium). Шаг `bundled_extensions` возьмёт ваши файлы из `resources/extensions/` и встроит их в браузер вместо загрузки с CDN. |

**Формат `bundled_extensions.json`** (один расширение — Agent):

```json
{
  "bflpfmnmnokmjhmgnolecpppdbdophmk": {
    "external_crx": "bflpfmnmnokmjhmgnolecpppdbdophmk.crx",
    "external_version": "1.0.0"
  }
}
```

Если вы упаковали без ключа и получили `agent-pack.crx` с **другим** ID, замените в JSON `bflpfmnmnokmjhmgnolecpppdbdophmk` на ваш ID и имя файла на `<ваш_id>.crx`.

**Итог:** после сборки браузера в панели «Assistant» будет ваше расширение с PonyAI (логотипы и текст). Без шагов 1–3 браузер подтянет расширения с CDN BrowserOS — будут старые иконки.

---

## Как проверить, что расширения встроены в собранный браузер

Путь к bundled-расширениям в рантайме — **рядом с бинарником** `chrome`:

- **Linux:** `<chromium_src>/out/Default_x64/browseros_extensions/`
- **macOS:** внутри `.app`: `…/Resources/browseros_extensions/`

Проверка (Linux, из каталога Chromium):

```bash
ls -la out/Default_x64/browseros_extensions/
```

Должны быть: `bundled_extensions.json` и файл(ы) `<extension_id>.crx` (например `hppcdefeenkjjbamdggkaaempenbljkn.crx` для Agent V2). Браузер при старте сначала пытается загрузить расширения из этой папки; если там есть .crx и манифест — CDN не используется.

Если в логах видно «Agent extension not found» или «PonyAI Agent is installing/updating» без результата — раньше загрузка из bundled была отключена в коде; после включения `TryLoadFromBundled()` расширение должно подхватываться из `browseros_extensions/`.

---

## Почему «Assistant» не в списке расширений и откуда старые логотипы

В сборке браузера кнопка **«Assistant»** в тулбаре — это **встроенное действие**: по клику открывается side panel **расширения Agent V2** (ID `bflpfmnmnokmjhmgnolecpppdbdophmk`). То есть контент панели («Agent at your service», логотипы, текст «BrowserOS») — это **UI именно расширения**, а не отдельная встроенная страница.

Расширение ставится в браузер как **bundled** (из .crx при сборке или с CDN). В `chrome://extensions` такие расширения могут не отображаться в списке «Мои расширения» или отображаться иначе — поэтому кажется, что «это не extension». На самом деле это то же расширение Agent, просто доставленное вместе с браузером.

**Откуда старые логотипы:** если в `packages/browseros/resources/extensions/` нет вашего .crx с PonyAI (или сборка браузера тянет расширения с CDN), в панели показывается **дефолтная** версия расширения (BrowserOS, старые иконки). Чтобы в панели были логотипы и брендинг PonyAI, нужно:

1. Собрать расширение с ребрендом (эта инструкция: скрипт `build_ponyai_extension.sh`, затем упаковать в .crx).
2. Положить .crx и `bundled_extensions.json` в `packages/browseros/resources/extensions/`.
3. Пересобрать браузер (шаг `bundled_extensions` скопирует ваш .crx в дерево Chromium вместо загрузки с CDN).

После этого при первом запуске/обновлении пользователь получит расширение с PonyAI, и в панели «Assistant» будут новые логотипы и текст.

## Что такое GraphQL и зачем он тут

Расширение (Agent) общается с **бэкендом** (API): сохраняет и загружает чаты, профиль, настройки провайдеров LLM, расписание задач и т.д. Этот API сделан в формате **GraphQL** — один HTTP-эндпоинт, запросы описываются в виде «что нужно получить/изменить».

- **Schema для codegen** можно взять **тремя способами:** (1) **встроенная** — в [BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent) после [PR #364](https://github.com/browseros-ai/BrowserOS-agent/pull/364) в репо есть `apps/agent/schema/schema.graphql`, тогда ничего в `.env` задавать не нужно; (2) **по URL** — в `.env.development` задать `GRAPHQL_SCHEMA_URL=https://api.browseros.com/graphql` (introspection); (3) **из файла** — `GRAPHQL_SCHEMA_PATH=/path/to/schema.graphql`.
- Наш скрипт подменяет `codegen.ts`: поддерживаются **`GRAPHQL_SCHEMA_URL`**, **`GRAPHQL_SCHEMA_PATH`** и fallback на **`schema/schema.graphql`** (как в PR #364). Репо workers не нужен.

То есть GraphQL тут — это **формат API бэкенда**. Чтобы собрать расширение: при использовании свежего BrowserOS-agent (с PR #364) достаточно клонировать репо и запустить сборку — codegen возьмёт встроенную схему. Либо задать в `apps/agent/.env.development` `GRAPHQL_SCHEMA_URL` или `GRAPHQL_SCHEMA_PATH`. Расширение при работе ходит на `VITE_PUBLIC_BROWSEROS_API` (или ваш API).

### Два разных агента: почему CONTRIBUTING «недостаточно» и откуда GraphQL

| | CONTRIBUTING.md (монорепо BrowserOS) | Наша сборка (репо BrowserOS-agent) |
|---|---|---|
| **Репо** | [BrowserOS](https://github.com/browseros-ai/BrowserOS) (один репо: браузер + агент) | [BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent) (отдельный репо) |
| **Путь к агенту** | `packages/browseros-agent` | `apps/agent` |
| **Сборка** | `yarn install` → `yarn build:dev` | `bun install` → `bun run codegen` → `bun run build` |
| **.env** | LITELLM_API_KEY | GRAPHQL_SCHEMA_PATH (+ порты, PostHog и т.д.) |
| **GraphQL** | Не упоминается — этот агент, судя по инструкции, не использует облачный API с GraphQL | **Используется:** чаты/профиль/провайдеры идут через GraphQL API. При сборке запускается **codegen**, которому нужна схема: по URL (introspection) или из файла. Репо BrowserOS-workers (где схема в исходниках) **приватный** (404), поэтому мы поддерживаем сборку **без workers** — через `GRAPHQL_SCHEMA_URL`. |

То есть **GraphQL появляется только во втором варианте**: агент из репо **BrowserOS-agent** общается с бэкендом через GraphQL. Официальная схема лежит в репо BrowserOS-workers, но он **не публичный** (страница даёт 404). Поэтому в нашем скрипте сборки мы подменяем `codegen.ts` и разрешаем брать схему по **URL** (introspection к `https://api.browseros.com/graphql` или ваш API) — репо workers клонировать не нужно.

**Итог:** инструкции из CONTRIBUTING.md недостаточно для сборки расширения «Assistant»: нужен репо **BrowserOS-agent** и шаги отсюда. Репо workers **не обязателен**: задайте `GRAPHQL_SCHEMA_URL` в `.env.development` и соберите скриптом.

## Что уже сделано в этом репо

- В клонированном агенте (`.cache/BrowserOS-agent`, после первого запуска `./scripts/build_ponyai_extension.sh`) **уже применён ребренд PonyAI**:
  - Заменены отображаемые строки: «BrowserOS» → «PonyAI», «Ask BrowserOS» → «Ask PonyAI», URL browseros.com → ponyai.com в константах и UI.
  - Логотипы скопированы из `packages/browseros/resources/icons` в `apps/agent/public/icon/` (16, 32, 48, 128) и `apps/agent/assets/product_logo.svg`.
- Сборка расширения **требует GraphQL codegen**. Скрипт подменяет `codegen.ts` так, что схему можно задать **по URL** (`GRAPHQL_SCHEMA_URL`) — репо BrowserOS-workers не нужен.

## Как собрать расширение у себя

1. **Задать схему для codegen** в `.env.development` агента (файл создаётся скриптом из `.env.example` при первом запуске, путь: `.cache/BrowserOS-agent/apps/agent/.env.development`). Достаточно **одного** из вариантов:
   - **Рекомендуется (без доступа к workers):** URL для introspection:
     ```bash
     GRAPHQL_SCHEMA_URL=https://api.browseros.com/graphql
     ```
     (Если API BrowserOS разрешает introspection, codegen получит схему сам. Если ваш бэкенд — свой, подставьте свой URL.)
   - **Либо** локальный путь к файлу схемы (если у вас есть `schema.graphql`):
     ```bash
     GRAPHQL_SCHEMA_PATH=/полный/путь/к/schema.graphql
     ```
   **Примечание:** из скомпилированного расширения (распакованный .crx) схему в виде файла достать нельзя — в сборке только бандлы JS. Если `GRAPHQL_SCHEMA_URL` не срабатывает (API отключил introspection), нужен файл схемы из другого источника (например от того, у кого есть доступ к workers).

**Сборка без облачного API:** если схему достать никак не получается, можно собрать расширение **без codegen**, с заглушками (облачные чаты/профиль/провайдеры при работе не будут синхронизироваться с API, но UI и локальные фичи соберутся). Запуск:
```bash
BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh
```
Скрипт подставит `scripts/agent-generated-stub/generated/graphql/` и вызовет только `wxt build`, без `bun run codegen`.

### Памятка: как мы собирали расширение (рабочий способ)

Использовали **сборку без облака** — без доступа к BrowserOS-workers и без GraphQL schema. Так собирается за ~1–2 минуты.

**Требования:** установлен **bun** (`curl -fsSL https://bun.sh/install | bash`).

**Одна команда (с логом в файл):**
```bash
cd /home/ubuntu/knx-west/aib/ai_browser
BUILD_AGENT_WITHOUT_CLOUD=1 ./scripts/build_ponyai_extension.sh 2>&1 | tee extension-build.log
```

**Что делает скрипт в этом режиме:**
- Клонирует/обновляет BrowserOS-agent в `.cache/BrowserOS-agent`.
- Применяет ребренд PonyAI и копирует иконки из `packages/browseros/resources/icons`.
- Подставляет заглушки: `scripts/agent-generated-stub/generated/graphql/` (вместо codegen) и `scripts/agent-env-build-fallback.ts` (env без zod).
- Отключает source maps в `wxt.config.ts` (чтобы сборка не зависала на тяжёлой фазе).
- Вызывает только `wxt build` (без `bun run codegen`).

**Если сборка «висит» (долго нет вывода, процесс грузит CPU):**
- Убить: `pkill -f "wxt build"`.
- Запустить команду выше заново. Без source maps сборка обычно доходит до конца за минуту-две.

**Результат:** распакованное расширение в `packages/browseros/resources/extensions/agent-build/`. Дальше: «Load unpacked» в Chrome или упаковать в .crx (см. ниже).

**Упаковка в .crx из консоли (без Chrome UI):**
```bash
./scripts/pack_agent_crx.sh
```
Нужен Node/npx (ставится с Node.js). Если есть ключ от предыдущей упаковки — положите его как `packages/browseros/resources/extensions/agent.pem` (или задайте `EXTENSION_PACK_KEY=/path/to/key.pem`); тогда получится `bflpfmnmnokmjhmgnolecpppdbdophmk.crx` с тем же ID и его можно сразу класть в `bundled_extensions.json`. Если ключа нет — скрипт создаст `agent-pack.crx` с новым ID; загрузите его в Chrome, узнайте ID, переименуйте в `<id>.crx` и обновите `bundled_extensions.json`.

2. **Собрать расширение** (ребренд уже применён скриптом при первом запуске):
   ```bash
   cd /home/ubuntu/knx-west/aib/ai_browser
   ./scripts/build_ponyai_extension.sh
   ```
   Скрипт клонирует/обновляет BrowserOS-agent, подменяет codegen (поддержка URL), применяет ребренд, копирует иконки, запускает `bun run codegen` и `bun run build` в `apps/agent`. Результат — в `packages/browseros/resources/extensions/agent-build/`.

3. **Упаковать в .crx** (чтобы браузер подтягивал расширение при сборке):
   - Открыть Chrome/Chromium → `chrome://extensions` → «Pack extension».
   - Выбрать папку: `packages/browseros/resources/extensions/agent-build`.
   - Указать ключ (или создать новый). Сохранить полученный `.crx` и, при необходимости, `.pem`.

4. **Положить файлы так, чтобы сборка браузера подтягивала расширение**:
   - Скопировать полученный `.crx` в `packages/browseros/resources/extensions/`.
   - Имя файла должно совпадать с ID расширения (как в `bundled_extensions.json`). Текущий ID Agent V2: `bflpfmnmnokmjhmgnolecpppdbdophmk`, т.е. файл: `bflpfmnmnokmjhmgnolecpppdbdophmk.crx`.
   - Положить в ту же папку `bundled_extensions.json` в формате:
     ```json
     {
       "bflpfmnmnokmjhmgnolecpppdbdophmk": {
         "external_crx": "bflpfmnmnokmjhmgnolecpppdbdophmk.crx",
         "external_version": "1.0.0"
       }
     }
     ```
   - При сборке браузера с `--prep` шаг `bundled_extensions` увидит файлы в `resources/extensions/` и скопирует их в дерево Chromium вместо загрузки с CDN — расширение будет подтягиваться при сборке.

## Где что менять при ребренде

- **Отображаемые имена и URL:** `wxt.config.ts` (default_title), `lib/constants/productUrls.ts`, `lib/constants/productWebHost.ts`, `lib/llm-providers/storage.ts`, `lib/llm-providers/providerTemplates.ts`, `entrypoints/onboarding/**`, `entrypoints/sidepanel/index/*.tsx`, `entrypoints/newtab/**`, `entrypoints/app/ai-settings/**`.
- **Иконки:** `apps/agent/public/icon/16.png`, `32.png`, `48.png`, `128.png` и `apps/agent/assets/product_logo.svg` — подменить файлами из `packages/browseros/resources/icons` (product_logo_*.png и product_logo.svg).
- **Не менять:** имена пакетов (`@browseros/agent`, `@browseros/server`), ключ в `wxt.config.ts` (от него зависит extension ID), тип провайдера `type: 'browseros'`, API браузера (`browserosIsOpen`, prefs `browseros.*`).
