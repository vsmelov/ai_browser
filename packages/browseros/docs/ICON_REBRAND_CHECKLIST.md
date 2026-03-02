# Чек-лист: иконки и ребрендинг PonyAI

## Как устроена подмена иконок

1. **Источники** лежат в `build/scripts/icon_generation/`:
   - `source/app_icon.png` — мастер PNG (≥1024×1024). Из него генерируются все PNG, ICO, ICNS, XPM.
   - `static/product_logo.svg` — векторный логотип (копируется в `resources/icons/` как есть).
   - `static/product_logo_animation.svg` — анимированный логотип (копируется как есть).
   - `static/product_logo.ai` — исходник в Illustrator (сейчас пустой файл).

2. **Скрипт** `python build/scripts/icon_generation/generate_icons.py`:
   - генерирует из `app_icon.png` все размеры в `resources/icons/` (product_logo_16.png … win/chromium.ico, mac/, linux/ и т.д.);
   - копирует `static/product_logo.svg` и `product_logo_animation.svg` в `resources/icons/` (перезаписывает существующие файлы).

3. **Сборка** по `copy_resources.yaml` копирует `resources/icons/` в дерево Chromium (`chrome/app/theme/chromium/` и т.д.). Код использует `IDR_PRODUCT_LOGO_16` и др. — ресурсы берутся из этой темы.

---

## Что проверить глазами (чтобы нигде не осталось старых иконок)

### 1. Мастер-иконка (обязательно)

| Файл | Назначение | Действие |
|------|------------|----------|
| `build/scripts/icon_generation/source/app_icon.png` | Все PNG, ICO, ICNS, XPM в сборке | Открыть и убедиться, что это **логотип PonyAI** (не оранжевый BrowserOS). Если нет — заменить на PonyAI 1024×1024. |

От этого файла зависят: иконка приложения (окно, панель задач), кнопка Assistant (IDR_PRODUCT_LOGO_16), все размеры product_logo_*.png, win/chromium.ico, mac/AppIcon, linux/product_logo_32.xpm и т.д.

### 2. Векторные логотипы в static/ (важно для SVG и копий)

| Файл | Назначение | Действие |
|------|------------|----------|
| `build/scripts/icon_generation/static/product_logo.svg` | Копируется в `resources/icons/product_logo.svg` при запуске generate_icons.py | Сейчас внутри **оранжевый BrowserOS** (#fb651f). Заменить содержимое на **PonyAI SVG**. |
| `build/scripts/icon_generation/static/product_logo_animation.svg` | Копируется в `resources/icons/product_logo_animation.svg` | То же — заменить на PonyAI. |
| `build/scripts/icon_generation/static/product_logo.ai` | Только копируется (сейчас пустой) | По желанию положить PonyAI .ai, если будете править логотип в Illustrator. |

Если не заменить static/*.svg и потом снова запустить `generate_icons.py`, то текущий большой `resources/icons/product_logo.svg` (166 KB, с base64) будет **перезаписан** маленьким BrowserOS-SVG из static.

### 3. Уже лежащие в репозитории файлы в resources/icons/

| Что | Комментарий |
|-----|-------------|
| `resources/icons/product_logo.svg` | Сейчас 166 KB (SVG с встроенным PNG). После замены static/product_logo.svg на PonyAI и запуска generate_icons.py будет перезаписан. Либо не запускать COPY и оставить этот файл вручную как PonyAI. |
| `resources/icons/product_logo_animation.svg` | Должен совпадать с static после generate_icons. Заменить исходник в static. |
| `resources/icons/linux/product_logo_32.xpm` | Генерируется из `app_icon.png`. Если app_icon.png — PonyAI, после перезапуска generate_icons будет PonyAI. |
| `resources/icons/mac/` | Только Contents.json в репо; appicon_*.png создаёт generate_icons из app_icon.png. Проверить после генерации. |

Остальных PNG/ICO в репо нет (они либо в .gitignore, либо создаются только при сборке). Имеет смысл после замены источников один раз запустить `generate_icons.py` и либо закоммитить результат, либо убедиться, что сборка его подхватывает.

### 4. Имена файлов (не контент)

| Место | Текущее имя | Примечание |
|-------|-------------|------------|
| `build/modules/package/linux.py` | `browseros.png` (в пути 256x256/apps/browseros.png и в AppDir) | Иконка по содержимому будет PonyAI, если заменили app_icon.png. Имя файла можно позже сменить на ponyai.png и поправить в linux.py. |

---

## Краткий порядок действий

1. Заменить **PonyAI** контентом:
   - `build/scripts/icon_generation/source/app_icon.png`
   - `build/scripts/icon_generation/static/product_logo.svg`
   - `build/scripts/icon_generation/static/product_logo_animation.svg`
2. Запустить:  
   `python build/scripts/icon_generation/generate_icons.py`  
   (из корня `packages/browseros`).
3. Убедиться, что сборка копирует сгенерированные `resources/icons/` в Chromium (copy_resources.yaml уже настроен).
4. При необходимости закоммитить обновлённые файлы в `resources/icons/` и в `icon_generation/source/` и `static/`.

После этого ни PNG, ни ICO, ни SVG в сборке не будут содержать старые иконки BrowserOS — только PonyAI.
