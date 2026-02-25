# Browser Build Guide (BrowserOS / Chromium)

Подробная инструкция по сборке своего AI-браузера на базе Chromium с использованием форка BrowserOS.

**Рабочая инструкция от нуля до запуска:** см. [QUICKSTART.md](QUICKSTART.md) — пошаговые команды без лишних деталей.

## Требуемая версия Chromium (git tag)

В репозитории задаётся файлом **`packages/browseros/CHROMIUM_VERSION`**:

- Текущее значение: **142.0.7444.49** (MAJOR.MINOR.BUILD.PATCH)
- Соответствующий **git tag в репозитории Chromium**: **142.0.7444.49**

При сборке скрипт читает этот файл и делает в вашей копии Chromium:
1. `git fetch --tags` в `chromium/src`
2. `git checkout tags/142.0.7444.49`
3. `gclient sync -D --no-history --shallow`

Убедитесь, что в вашем клоне Chromium есть тег `142.0.7444.49` (он появится после `git fetch --tags` в chromium/src).

### Синхронизация Chromium на нужный тег (gclient sync)

Команду выполняйте из каталога, где лежит `.gclient` (родитель `src`), например `~/knx-west/aib/chromium`:

```bash
cd ~/knx-west/aib/chromium   # или ваш путь к папке с .gclient и src/
gclient sync -j8 -v --no-history --revision=src@refs/tags/142.0.7444.49
```

После синка для сборки BrowserOS передавайте путь к **src**: `--chromium-src /home/ubuntu/knx-west/aib/chromium/src`.

**Типичная раскладка (Chromium на папку выше репозитория):**

```
~/knx-west/aib/
├── ai_browser/     # форк BrowserOS
├── chromium/       # .gclient и src/ здесь
│   └── src/
└── depot_tools/
```

Путь к исходникам для сборки: `~/knx-west/aib/chromium/src`.

---

## 1. Зависимости, которые нужно «склонировать» / установить

### 1.1 Репозиторий BrowserOS (у вас уже есть)

- Ваш форк: `git@github.com:vsmelov/ai_browser.git`
- Ветка: `main`, рабочее дерево чистое
- **Тегов в этом репозитории нет** — теги используются в репозитории **Chromium**, не в BrowserOS

### 1.2 Chromium (отдельно, ~100 GB)

Chromium **не входит** в репозиторий BrowserOS. Его нужно получить по официальной инструкции:

1. **Установить depot_tools**
   - https://www.chromium.org/developers/how-tos/get-the-code/
   - Клонировать: `git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git`
   - Добавить `depot_tools` в `PATH` (в начале):  
     `export PATH="/path/to/depot_tools:$PATH"`

2. **Получить исходники Chromium**
   - Создать каталог для клона (например `chromium`), перейти в него
   - Выполнить:
     ```bash
     fetch chromium
     ```
   - Или только `src`:
     ```bash
     fetch --no-history chromium
     ```
   - Это займёт много времени и ~100 GB места.

3. **Проверить тег Chromium**
   - После `fetch` в `src` выполнить:
     ```bash
     cd src
     git fetch --tags --force
     git tag -l "142.0.7444.49"
     ```
   - Должен появиться тег `142.0.7444.49`. Версия в `packages/browseros/CHROMIUM_VERSION` должна совпадать с этим тегом.

### 1.3 Агент (Chrome-расширение) — ядро BrowserOS

**Агент — это и есть главная часть BrowserOS:** AI-панель, инструменты автоматизации, MCP, Workflows, LLM Hub и т.д. Без агента вы получаете только оболочку Chromium с патчами, без AI-функций.

- **Путь в монорепо:** `packages/browseros-agent/`
- **Зависимости:** Node.js 18+, yarn → `yarn install` в каталоге агента
- **Сборка расширения:** `yarn build:dev` (или production-сборка по инструкции в репозитории)

**Когда агент «уже есть» в сборке:**
- В **релизной** сборке браузера используется шаг `bundled_extensions`: расширения **скачиваются с CDN** по манифесту. То есть бинарник браузера можно собрать без исходников агента — в него попадёт версия расширения с серверов BrowserOS.
- Для **своего форка** или **разработки** нужны исходники агента: вы собираете расширение локально и подключаете его (Load unpacked в `chrome://extensions/` или своя логика бандлинга). Иначе у вас не будет своей AI-логики и своего UI.

Если в вашем форке нет папки `packages/browseros-agent/`, её нужно взять из upstream [browseros-ai/BrowserOS](https://github.com/browseros-ai/BrowserOS) (или склонировать монорепо целиком и собирать из него).

**Для первого запуска** проще не трогать исходники агента: в релизной сборке (`release.linux.yaml` и др.) шаг `bundled_extensions` сам подтянет расширение с CDN — собранный браузер уже будет с рабочим агентом. Исходники агента понадобятся, когда будете менять логику/UI или собирать свой форк расширения.

**Итог по зависимостям:**
- **BrowserOS** — склонирован (ваш форк).
- **Chromium** — отдельно: depot_tools + `fetch chromium` и тег `142.0.7444.49`.
- **Агент** — обязателен для полного продукта; для релизного бинарника подтягивается с CDN, для своей сборки/форка нужны исходники в `packages/browseros-agent/`.
- **Правильный git tag** — тег **в репозитории Chromium** `142.0.7444.49` (см. `packages/browseros/CHROMIUM_VERSION`).

---

## 2. Дальнейшие шаги: собрать свой AI browser на базе Chromium

### Шаг 1: Установить depot_tools и получить Chromium

```bash
# Пример (подставьте свой путь)
export PATH="/path/to/depot_tools:$PATH"
mkdir -p /path/to/chromium && cd /path/to/chromium
fetch --no-history chromium
```

Дождаться окончания загрузки.

### Шаг 2: Проверить тег в Chromium

```bash
cd /path/to/chromium/src
git fetch --tags --force
git tag -l "142.0.7444.49"
# Должен вывести: 142.0.7444.49
```

Если тега нет — в Chromium могли переименовать/обновить версии; тогда нужно обновить `packages/browseros/CHROMIUM_VERSION` под существующий тег (см. вывод `git tag -l` и официальные теги Chromium).

### Шаг 3: Сборка из репозитория BrowserOS

Перейти в пакет сборки и запустить сборку, указав путь к **Chromium src**. Запуск — всегда из **`packages/browseros`** (репозиторий ai_browser), не из папки Chromium.

#### Официальный способ (docs.browseros.com)

В [официальной документации BrowserOS](https://docs.browseros.com/contributing#path-2-browser-development) рекомендуют **UV** и флаги фаз (без YAML-конфига):

```bash
# 1. Установить UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Перейти в пакет сборки и установить зависимости
cd ~/knx-west/aib/ai_browser/packages/browseros
uv sync

# 3. Первая сборка (setup + prep + build)
uv run browseros build \
  --chromium-src /home/ubuntu/knx-west/aib/chromium/src \
  --setup --prep --build --build-type debug

# С выводом в лог-файл:
# uv run browseros build --chromium-src /path/to/chromium/src --setup --prep --build --build-type debug 2>&1 | tee out.log

# 4. Следующие сборки (только компиляция)
uv run browseros build --chromium-src /home/ubuntu/knx-west/aib/chromium/src --build --build-type debug
```

Флаги: `--setup` и `--prep` — только для первого раза; дальше достаточно `--build --build-type debug`. Запуск собранного браузера (Linux):  
`<chromium-src>/out/Default_x64/browseros --enable-logging=stderr --user-data-dir=/tmp/test-profile`

#### Альтернатива: сборка по YAML-конфигу

Можно вместо флагов использовать конфиг (например `debug.linux.yaml`): тогда пайплайн задаётся списком модулей в YAML. Подходит для CI или если нужен тот же набор шагов, что в release.

**Debug vs Release (в чём разница и почему debug быстрее)**

| | Debug | Release |
|---|--------|--------|
| **Цель** | Разработка, отладка | Продакшен, распространение |
| **Оптимизация** | Минимальная (`is_debug=true`) | Полная (`is_official_build=true`) |
| **Символы** | Включены (`symbol_level=1`) — удобно для отладчика | Выключены (`symbol_level=0`) — меньший размер бинарника |
| **Проверки** | `DCHECK` включены (`dcheck_always_on=true`) — падения на некорректных данных | `DCHECK` выключены — быстрее работа, меньше диагностики |
| **Сборка** | **Быстрее**: компилятор почти не оптимизирует, меньше проходов | **Дольше**: агрессивная оптимизация (-O2/-O3), больше времени на каждый файл |

Итог: debug-сборка **компилируется быстрее** (меньше работы компилятора) и даёт **удобный отладочный бинарник**; release — дольше собирается, но бинарник быстрее работает и меньше по размеру. Для первого запуска и проверки пайплайна можно использовать любую; для итераций по коду удобнее debug.

**Linux (release)** — при раскладке `~/knx-west/aib/{ai_browser,chromium}`:
```bash
cd ~/knx-west/aib/ai_browser/packages/browseros
python -m build.browseros build --config build/config/release.linux.yaml --chromium-src /home/ubuntu/knx-west/aib/chromium/src --build
```

**Linux (debug)** — конфиг `debug.linux.yaml` есть в репо:
```bash
cd ~/knx-west/aib/ai_browser/packages/browseros
python -m build.browseros build --config build/config/debug.linux.yaml --chromium-src /home/ubuntu/knx-west/aib/chromium/src --build
```
Файл `debug.yaml` в `config/` — только для **macOS** (там `flags.macos.debug.gn` и `package_macos`). Для Linux используйте именно `debug.linux.yaml`.

**macOS:**
```bash
cd ~/knx-west/aib/ai_browser/packages/browseros
python -m build.browseros build --config build/config/debug.macos.yaml --chromium-src /path/to/chromium/src --build
# или release.macos.yaml для релиза
```

**Windows:**
```bash
cd ~/knx-west/aib/ai_browser/packages/browseros
python -m build.browseros build --config build/config/debug.windows.yaml --chromium-src /path/to/chromium/src --build
```

**Альтернатива:** после `pip install -e .` в `packages/browseros` можно вызывать команду `browseros`:
```bash
browseros build --config build/config/debug.linux.yaml --chromium-src /home/ubuntu/knx-west/aib/chromium/src --build
```

Первый прогон выполняет в том числе:
- `git_setup` — checkout тега из `CHROMIUM_VERSION` и `gclient sync`
- **патчи и правки прямо в дереве Chromium** (в каталоге `--chromium-src`): патчи из `chromium_patches/`, подмена файлов из `chromium_files/`, копирование ресурсов и расширений, замена строк брендинга
- `configure` (gn) и `compile` (ninja)
- упаковку (package_linux / package_macos / package_windows)

**Важно:** дерево Chromium в `--chromium-src` при сборке изменяется (патчи, копирование, замены). Если нужна нетронутая копия upstream — перед первым запуском сделайте копию `chromium/src` или клонируйте отдельную директорию под BrowserOS.

**Если патчи падают** (`does not exist in index`, `patch does not apply`, `does not match index`) — дерево в смешанном состоянии (часть патчей применена, часть нет). Надёжный способ: один раз запустить с **`--setup`** (очистка + checkout тега + gclient sync), затем `--prep --build`. Без `--setup` повторный `--prep` может не исправить ситуацию.

**R2 и бинарник browseros-server:** см. отдельный раздел ниже [«BrowserOS server и R2»](#31-browseros-server-бинарник-и-r2).

Сборка может занять 1–3 часа в зависимости от железа.

---

### BrowserOS server бинарник и R2 {#browseros-server-бинарник-и-r2}

**Заметка:** чтобы не путать «агента» и сервер — см. [docs/BROWSEROS_SERVER.md](BROWSEROS_SERVER.md): мы собираем бинарник **сервера** (apps/server из репо BrowserOS-agent), не Chrome-расширение.

**Что такое browseros_server:** это нативный исполняемый файл (MCP/CDP-сервер), который Chromium запускает как отдельный процесс. Он принимает запросы от агента (расширения), общается с CDP (Chrome DevTools Protocol) и контроллер-расширением по WebSocket. Исходники сервера — в отдельном репозитории [browseros-ai/BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent) (Bun/TypeScript, `apps/server`). Официальные бинарники BrowserOS собирает скриптом `scripts/build/server.ts` (Bun `build --compile`) и заливает их в **Cloudflare R2**.

**Подключиться к их R2 нельзя** без выданных ими ключей. R2 — приватный бакет BrowserOS; переменные `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` в открытом доступе не публикуются. То есть «подключиться к их R2» в смысле использовать их бакет может только их CI/команда.

**Что можно сделать:**

1. **Запросить доступ у BrowserOS**  
   Написать в [Discord](https://discord.gg/browseros) или [GitHub Issues](https://github.com/browseros-ai/BrowserOS/issues): попросить read-only ключи R2 или публичную ссылку на скачивание бинарников `browseros-server-*`. Если дадут ключи — задать их в окружении перед сборкой; тогда шаг `download_resources` скачает бинарник сам.

2. **Собрать browseros_server из исходников**  
   Нужны только [Bun](https://bun.sh) и git. Из корня репозитория:
   ```bash
   ./scripts/build_browseros_server.sh
   ```
   Скрипт при первом запуске клонирует [BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent) в `.cache/BrowserOS-agent`, соберёт сервер в режиме `--mode=dev` для текущей платформы и положит бинарник в `packages/browseros/resources/binaries/browseros_server/`. Дальше сборка браузера подхватит его при копировании ресурсов.
   - Использовать уже склонированный агент: `BROWSEROS_AGENT_DIR=/path/to/BrowserOS-agent ./scripts/build_browseros_server.sh`
   - Собрать другой таргет: `TARGET=linux-arm64 ./scripts/build_browseros_server.sh` (доступны `linux-x64`, `linux-arm64`, `darwin-arm64`, `darwin-x64`, `windows-x64`).
   Ручная сборка без скрипта: клонировать BrowserOS-agent, `bun install`, `bun scripts/build/server.ts --mode=dev --target=linux-x64`, скопировать `dist/server/browseros-server-*` в `packages/browseros/resources/binaries/browseros_server/`. Имена файлов — в `copy_resources.yaml`.

3. **Сборка без бинарника**  
   Если R2 не настроен и бинарник не положен вручную — шаг `download_resources` пропускается, при копировании ресурсов создаётся **заглушка** в `chrome/browser/browseros/server/resources/bin/browseros_server`, чтобы GN/ninja не падали. Браузер соберётся и запустится, но MCP/CDP-сервер работать не будет до появления настоящего бинарника.

### Шаг 4: Переменная окружения (опционально)

Чтобы не указывать `--chromium-src` каждый раз:

```bash
export CHROMIUM_SRC=/path/to/chromium/src
```

В YAML можно задать `chromium_src: !env CHROMIUM_SRC`, тогда путь возьмётся из переменной.

### Шаг 5: Свой брендинг и код

- **Версия Chromium:** правьте `packages/browseros/CHROMIUM_VERSION` (должна соответствовать существующему тегу в Chromium).
- **Строки и ресурсы:** `packages/browseros/build/config/`, ресурсы в `packages/browseros/resources/`.
- **Патчи в код Chromium:** `packages/browseros/chromium_patches/`.
- **Иконки и подмены файлов:** см. `copy_resources.yaml`, `chromium_replace`, `chromium_files/`.

---

## 3. Краткий чеклист

| Что проверить | Статус |
|---------------|--------|
| Репозиторий BrowserOS склонирован | ✅ Ваш форк, ветка main |
| Git-тег для сборки | Тег в **Chromium**: `142.0.7444.49` (из `CHROMIUM_VERSION`) |
| Chromium исходники | Нужно отдельно: depot_tools + `fetch chromium` |
| Путь к Chromium | Передавать в `--chromium-src` или через `CHROMIUM_SRC` |
| Документация по сборке | README + CONTRIBUTING.md; этот файл — доп. гайд |

После выполнения шагов 1–3 у вас будет собран бинарник своего AI-браузера на базе Chromium с патчами и ресурсами BrowserOS.
