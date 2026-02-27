# Переименование браузера и замена логотипа

Как сменить имя приложения и поставить свой логотип: какие файлы менять и куда класть картинки.

---

## 1. Имя приложения (переименование браузера)

Имя используется в заголовках окон, меню «О программе», пакетах (.deb, .AppImage, .dmg), ярлыках и т.д.

### 1.1 Главное место — базовое имя

**Файл:** `packages/browseros/build/common/context.py`

- **Поле:** `BROWSEROS_APP_BASE_NAME` (по умолчанию `"BrowserOS"`).
- **Где задаётся:** в классе `PathConfig` (строка ~157) и в классе `Context` (строка ~202).
- **Что делать:** заменить `"BrowserOS"` на своё имя (например `"PonyAI"`). От этого имени выводятся:
  - имя бинарника (Linux: `browseros` → `ponyai`),
  - имя .app (macOS: `BrowserOS.app` → `PonyAI.app`),
  - имя .exe (Windows),
  - пути в пакетах (AppDir, .deb и т.д.).

Сейчас значение захардкожено в коде. Чтобы задавать имя из конфига, нужно добавить чтение из YAML в `resolver.py` и передачу в `Context`.

### 1.2 Строковые подстановки в Chromium

**Файл:** `packages/browseros/build/modules/resources/string_replaces.py`

- **Переменная:** `branding_replacements` — список пар (регулярка → замена).
- **Сейчас:** «Chromium» → «BrowserOS», «Chrome» → «BrowserOS», «Google Chrome» → «BrowserOS» и т.д.
- **Что делать:** заменить правую часть на своё имя (например `r"BrowserOS"` → `r"PonyAI"`).
- **Файлы в Chromium, куда применяется:** пути заданы в `target_files`:
  - `chrome/app/chromium_strings.grd`
  - `chrome/app/settings_chromium_strings.grdp`

Там лежат строки интерфейса (название в меню, «О программе» и т.д.).

### 1.3 Брендинг Chromium (BRANDING)

**Каталог:** `packages/browseros/chromium_files/chrome/app/theme/chromium/`

- **Файлы:** `BRANDING.release`, `BRANDING.debug`
- **Содержимое:** `COMPANY_FULLNAME`, `PRODUCT_FULLNAME`, `PRODUCT_SHORTNAME`, `PRODUCT_INSTALLER_*`, `COPYRIGHT`, `MAC_BUNDLE_ID` и т.д.
- **Что делать:** заменить `BrowserOS` на своё имя во всех полях. Для macOS поменять `MAC_BUNDLE_ID` (например `com.browseros.BrowserOS` → `com.yourapp.PonyAI`).

### 1.4 Linux: .desktop, .deb, AppImage

**Файл:** `packages/browseros/build/modules/package/linux.py`

Жёстко прописаны строки (их нужно менять при смене имени):

| Что | Строка/место | Пример значения |
|-----|----------------|------------------|
| Имя в .desktop | `Name=...`, `Icon=...` | `Name=BrowserOS`, `Icon=browseros` |
| Имя файла .desktop | `desktop_file = ... "browseros.desktop"` | `browseros.desktop` |
| Иконка в hicolor | `"browseros.png"` | `256x256/apps/browseros.png` |
| Иконка в AppDir | `appdir_icon = "browseros.png"` | `browseros.png` |
| Launcher в /usr/bin | `launcher_path = "browseros"` | `browseros` |
| Package name в control | `Package: browseros` | `browseros` |
| Description в control | `BrowserOS - The open source...` | текст описания |
| Maintainer / Homepage | `BrowserOS Team`, `browseros.com` | свои данные |
| Postinst | `# Post-installation script for BrowserOS` | комментарий |

Имеет смысл завести переменные от `ctx.BROWSEROS_APP_BASE_NAME` (например имя пакета и desktop — в нижнем регистре от базового имени), а явные «BrowserOS» в описаниях заменить на подстановку из контекста или один раз поменять вручную при ребрендинге.

### 1.5 macOS / Windows

- **macOS:** в `packages/browseros/build/modules/package/macos.py` и `packages/browseros/build/modules/sign/macos.py` встречаются `"BrowserOS"`, `volume_name="BrowserOS"`, `com.browseros.BrowserOS` — заменить на своё имя и bundle id.
- **Windows:** в `packages/browseros/build/modules/package/windows.py` и `packages/browseros/build/modules/sign/windows.py` — аналогично поиск по `BrowserOS` и замена.

### 1.6 Релизы и OTA

- **Release:** `packages/browseros/build/modules/release/common.py` — пути вида `download/BrowserOS-arm64.dmg`, заголовки «BrowserOS - {version}», текст релиз-нотов.
- **OTA:** `packages/browseros/build/modules/ota/common.py` — «BrowserOS Server», описание обновлений.

При ребрендинге в этих модулях тоже заменить имя и при необходимости пути.

### 1.7 После ребрендинга: перекомпиляция

Перепатчивать Chromium заново не нужно — достаточно **перезапустить prep**, чтобы в дерево Chromium подтянулись новый брендинг (BRANDING, string_replaces) и при необходимости патчи. Полный `--setup` (clean) **не запускайте**: он делает `git reset --hard` в каталоге Chromium и откатит все изменения (брендинг и патчи), после чего пришлось бы заново качать/патчить дерево.

**Рекомендуемый порядок:**

1. **Только prep + build (переиспользуем дерево):**
   ```bash
   browseros build --prep --build
   ```
   Prep перезапишет BRANDING и применит string_replaces (BrowserOS → PonyAI) в GRD; configure обновит аргументы GN. Ninja пересоберёт изменённые ресурсы и зависимости. Обычно этого достаточно.

2. **Если хотите пересобрать бинарники с нуля (без очистки дерева Chromium):**
   - Удалить каталог сборки в дереве Chromium, например:
     ```bash
     rm -rf /путь/к/chromium/src/out/Default
     ```
   - Затем:
     ```bash
     browseros build --prep --build
     ```

После перекомпиляции бинарник (Linux: `ponyai`), .app (macOS: `PonyAI.app`), пакеты и строки интерфейса должны соответствовать новому имени (PonyAI).

### 1.8 Chrome-расширение (Assistant / Agent)

Popup расширения («Assistant», «BrowserOS», иконки) **не собирается в этом репо** — по умолчанию сборка **скачивает** готовые .crx с CDN (cdn.browseros.com). Чтобы в расширении был брендинг PonyAI и свои логотипы:

1. **Исходники расширения** — в репозитории [BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent): приложения `apps/agent` (чат/панель Assistant) и при необходимости `apps/controller-ext`. Там нужно заменить текст «BrowserOS» на «PonyAI» и подставить свои иконки (в нужных размерах для popup и манифеста).

2. **Локальные расширения (рекомендуется для ребренда):** положите свои .crx и манифест в каталог:
   - **`packages/browseros/resources/extensions/`**
   - В нём должны быть:
     - `bundled_extensions.json` — в том же формате, что генерирует сборка (ключ = extension id, значение `external_crx`, `external_version`).
     - Файлы `<extension_id>.crx` для каждого расширения (например `bflpfmnmnokmjhmgnolecpppdbdophmk.crx` для Agent V2).
   - При наличии этого каталога сборка **не качает** расширения с CDN, а копирует файлы из `resources/extensions/` в дерево Chromium.

3. **Как получить .crx с PonyAI:** из корня репо выполнить `./scripts/build_ponyai_extension.sh`. Скрипт клонирует BrowserOS-agent, заменит «BrowserOS» на «PonyAI» и подставит иконки из `packages/browseros/resources/icons`, соберёт расширение и скопирует его в `packages/browseros/resources/extensions/agent-build/`. Дальше: загрузить как «Load unpacked» из `agent-build/` или упаковать в .crx (Chrome → Extensions → Pack extension) и положить .crx в `resources/extensions/` вместе с `bundled_extensions.json`.

Подробнее про сервер и агент — в [BROWSEROS_SERVER.md](BROWSEROS_SERVER.md).

---

## 2. Логотип и иконки

Иконки копируются в дерево Chromium из одного каталога и опционально подменяются через `chromium_files`.

### 2.1 Источник иконок (основной)

**Каталог:** `packages/browseros/resources/icons/`

Сборка копирует отсюда файлы в Chromium согласно `packages/browseros/build/config/copy_resources.yaml`. Пути относительно `packages/browseros/`.

| Что копируется | Источник (source) | Куда в Chromium (destination) |
|----------------|-------------------|---------------------------------|
| PNG в корне icons | `resources/icons/*.png` | `chrome/app/theme/chromium/` |
| AI | `resources/icons/*.ai` | `chrome/app/theme/chromium/` |
| SVG | `resources/icons/*.svg` | `chrome/app/theme/chromium/` |
| ChromeOS | `resources/icons/chromeos` | `chrome/app/theme/chromium/chromeos` |
| Linux | `resources/icons/linux` | `chrome/app/theme/chromium/linux` |
| macOS | `resources/icons/mac` | `chrome/app/theme/chromium/mac` |
| Windows | `resources/icons/win` | `chrome/app/theme/chromium/win` |
| 100% DPI | `resources/icons/default_100_percent` | `chrome/app/theme/default_100_percent/chromium` |
| 200% DPI | `resources/icons/default_200_percent` | `chrome/app/theme/default_200_percent/chromium` |

Имена файлов не должны меняться, если не правишь конфиг копирования: Chromium ожидает определённые имена (например `product_logo_24.png`, `product_logo.svg`). Меняешь только содержимое файлов — подставляешь свой логотип в нужных размерах.

### 2.2 Релевантные файлы для замены логотипа

Заменить файлы (сохраняя имена и форматы):

**В корне `resources/icons/`:**
- `product_logo.png` — общий логотип (используется, в частности, для Linux в .deb/AppImage как `product_logo.png`).
- `product_logo.svg`, `product_logo.ai` — векторные варианты.
- `product_logo_16.png`, `product_logo_22.png`, `product_logo_24.png`, `product_logo_32.png`, `product_logo_48.png`, `product_logo_64.png`, `product_logo_128.png`, `product_logo_192.png`, `product_logo_256.png`, `product_logo_1024.png` — растровые размеры.
- `product_logo_name_22.png`, `product_logo_name_22_2x.png`, `product_logo_name_22_white.png`, `product_logo_name_22_white_2x.png` — варианты с названием/белые.
- `product_logo_22_mono.png` — монохромный вариант.
- `product_logo_animation.svg` — анимация (если нужна).

**В подкаталогах:**
- `default_100_percent/` — `product_logo_16.png`, `product_logo_32.png`, `product_logo_name_22.png`, `product_logo_name_22_white.png`; в `linux/` — те же имена.
- `default_200_percent/` — те же имена (обычно в 2x разрешении).
- `linux/` — `product_logo_24.png`, `product_logo_32.xpm`, `product_logo_48.png`, `product_logo_64.png`, `product_logo_128.png`, `product_logo_256.png`.
- `mac/` — `AppIcon.icns`, `app.icns`, `document.icns`, `Assets.car` и содержимое `Assets.xcassets/AppIcon.appiconset/` (appicon_16.png … appicon_1024.png).
- `win/` — `chromium.ico`, `chromium_doc.ico`, `app_list.ico`, `chromium_pdf.ico`, `incognito.ico`, `tiles/Logo.png`, `tiles/SmallLogo.png`.

Минимально для «просто поменять логотип» обычно достаточно обновить основные растры в корне и в `default_100_percent/`, `default_200_percent/`, `linux/`, а также `product_logo.png`. Остальное — по мере необходимости (macOS/Windows/ChromeOS).

### 2.3 Дополнительно: chromium_files (подмена файлов в Chromium)

**Каталог:** `packages/browseros/chromium_files/`

Структура каталогов должна повторять путь в дереве Chromium. Файлы из `chromium_files/` копируются поверх дерева Chromium на этапе `chromium_replace` (до или вместе с копированием ресурсов — смотри порядок модулей в конфиге).

Если нужно подменить конкретный файл темы, который уже попал в Chromium из `resources/icons/`, можно положить свой файл с тем же путём относительно `chromium_files/`, например:
- `chromium_files/chrome/app/theme/chromium/product_logo_24.png`

Тогда при сборке он перезапишет файл в `chromium/src/chrome/app/theme/chromium/product_logo_24.png`. Основной источник иконок всё равно `resources/icons/` и `copy_resources.yaml`; `chromium_files` — для точечных переопределений.

### 2.4 Логотип в корне репозитория

**Файл:** `packages/browseros/resources/logo.png`

Используется в документации или скриптах (не в самой сборке Chromium). При ребрендинге можно заменить на свой логотип.

---

## 3. Порядок действий (кратко)

1. **Имя приложения**
   - Поменять `BROWSEROS_APP_BASE_NAME` в `context.py`.
   - Обновить `branding_replacements` в `string_replaces.py`.
   - Обновить `BRANDING.release` и `BRANDING.debug` в `chromium_files/chrome/app/theme/chromium/`.
   - Пройтись по `linux.py`, `macos.py`, `windows.py`, `release/common.py`, `ota/common.py`, sign-модулям — заменить все вхождения старого имени и при необходимости bundle id / пути.

2. **Логотип**
   - Подготовить свой логотип в нужных размерах и форматах.
   - Подменить файлы в `packages/browseros/resources/icons/` (и при необходимости в подкаталогах), сохраняя имена файлов.
   - При необходимости положить переопределения в `packages/browseros/chromium_files/chrome/app/theme/chromium/`.
   - При желании обновить `packages/browseros/resources/logo.png`.

3. **Сборка**
   - Запустить сборку с `--prep` (чтобы применились string_replaces и скопировались ресурсы/иконки). Например:  
     `uv run browseros build --chromium-src <path> --prep --build --build-type debug`

4. **Проверка**
   - Запустить собранный бинарник, проверить заголовок окна, «О программе», иконку в панели/рабочем столе и в установщиках (.deb, AppImage, .dmg, .exe).

---

## 4. Сводная таблица путей

| Назначение | Путь |
|------------|------|
| Базовое имя приложения | `packages/browseros/build/common/context.py` — `BROWSEROS_APP_BASE_NAME` |
| Строки в UI Chromium | `packages/browseros/build/modules/resources/string_replaces.py` — `branding_replacements`, `target_files` |
| Брендинг (product name, bundle id) | `packages/browseros/chromium_files/chrome/app/theme/chromium/BRANDING.release`, `BRANDING.debug` |
| Конфиг копирования иконок | `packages/browseros/build/config/copy_resources.yaml` |
| Иконки (основной каталог) | `packages/browseros/resources/icons/` |
| Подмена файлов в Chromium | `packages/browseros/chromium_files/` (структура как в chromium/src) |
| Логотип для доки/прочее | `packages/browseros/resources/logo.png` |
| Linux .desktop / .deb / AppImage | `packages/browseros/build/modules/package/linux.py` |
| macOS DMG / подпись | `packages/browseros/build/modules/package/macos.py`, `sign/macos.py` |
| Windows installer / подпись | `packages/browseros/build/modules/package/windows.py`, `sign/windows.py` |
| Релизные пути и тексты | `packages/browseros/build/modules/release/common.py` |
| OTA (сервер) | `packages/browseros/build/modules/ota/common.py` |

После изменений пересобери с `--prep --build`. **Если при этом патчи падают** («does not match index») — дерево Chromium уже пропатчено. Тогда для смены **только логотипов/ресурсов** не трогай патчи, запусти только копирование ресурсов и сборку:

```bash
cd ~/knx-west/aib/ai_browser/packages/browseros
uv run browseros build --chromium-src /path/to/chromium/src \
  --modules download_resources,resources,bundled_extensions,chromium_replace,string_replaces,configure,compile \
  --build-type debug
```

(подставь свой путь к `chromium/src`). Так патчи не применяются заново, обновляются только иконки/строки и идёт инкрементальная компиляция — обычно несколько минут, а не 2 часа. Полный `--setup --prep --build` нужен только когда дерево сломано или сменили версию Chromium.
