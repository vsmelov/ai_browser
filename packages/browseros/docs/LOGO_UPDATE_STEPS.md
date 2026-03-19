# Как везде прокинуть новый логотип (PonyClaw)

Пошагово: от источника до браузера и расширения.

---

## 1. Источник — один раз заменить

| Файл | Действие |
|------|----------|
| `packages/browseros/build/scripts/icon_generation/source/app_icon.png` | Заменить на логотип PonyClaw **1024×1024** (или больше). От него генерируются все PNG/ICO/XPM. |
| `packages/browseros/build/scripts/icon_generation/static/product_logo.svg` | Заменить на PonyClaw SVG (иначе при следующей генерации перезатрёт большой product_logo.svg в resources). |
| `packages/browseros/build/scripts/icon_generation/static/product_logo_animation.svg` | То же — PonyClaw. |

---

## 2. Сгенерировать все размеры

Из корня **packages/browseros**:

```bash
cd packages/browseros
python build/scripts/icon_generation/generate_icons.py
```

Скрипт создаёт/обновляет в `resources/icons/`:

- `product_logo_16.png`, `product_logo_32.png`, …, `product_logo_1024.png`
- `default_100_percent/product_logo_16.png`, `default_100_percent/linux/product_logo_16.png`, …
- `default_200_percent/product_logo_16.png`, …
- `win/chromium.ico`, `linux/product_logo_32.xpm`, `mac/` и т.д.

Проверь глазами, что в `resources/icons/product_logo_16.png` и в `resources/icons/default_100_percent/linux/product_logo_16.png` — новый логотип.

---

## 3. Скопировать ресурсы в дерево Chromium

Копирование задано в `build/config/copy_resources.yaml`. Оно запускается при **сборке** (модуль Resources), когда в конфиге сборки включён этап копирования ресурсов (обычно при `--setup` или при полной сборке).

Вручную (если нужно только обновить иконки без полной сборки):

- Либо снова запустить тот же шаг сборки, который вызывает copy_resources (зависит от вашего build CLI).
- Либо скопировать вручную из `packages/browseros/resources/icons/` в дерево Chromium:

```bash
# Из корня ai_browser, CHROMIUM_SRC — путь к chromium/src
CHROMIUM_SRC=/path/to/chromium/src
BROWSEROS=packages/browseros

cp -r $BROWSEROS/resources/icons/*.png    $CHROMIUM_SRC/chrome/app/theme/chromium/
cp -r $BROWSEROS/resources/icons/linux    $CHROMIUM_SRC/chrome/app/theme/chromium/
cp -r $BROWSEROS/resources/icons/default_100_percent/*  $CHROMIUM_SRC/chrome/app/theme/default_100_percent/chromium/
cp -r $BROWSEROS/resources/icons/default_200_percent/*  $CHROMIUM_SRC/chrome/app/theme/default_200_percent/chromium/
```

**Важно:** в Chromium для Linux также ожидается `chrome/app/theme/chromium/linux/product_logo_16.png`. Сейчас `copy_resources` копирует каталог `resources/icons/linux` в `chromium/linux`, но в `resources/icons/linux/` нет `product_logo_16.png` (там только xpm и другие размеры). Файл 16px лежит в `resources/icons/default_100_percent/linux/product_logo_16.png`. Имеет смысл один раз скопировать его вручную в Chromium:

```bash
cp $BROWSEROS/resources/icons/default_100_percent/linux/product_logo_16.png \
   $CHROMIUM_SRC/chrome/app/theme/chromium/linux/
```

(или добавить в generate_icons / copy_resources копирование 16px в `resources/icons/linux/`).

---

## 4. Пересобрать браузер

После обновления файлов в `chrome/app/theme/chromium/` и т.д. нужна **пересборка** (хотя бы цели, зависящие от theme resources), чтобы ресурсы попали в бинарник. Обычно достаточно инкрементальной сборки.

Итог: в браузере кнопка «Pony» (IDR_PRODUCT_LOGO_16), иконка окна, иконки в настройках и т.д. будут из нового логотипа.

---

## 5. Расширение (сайдбар «Pony»)

Иконка в тулбаре браузера — из шагов 1–4. Иконка **самого расширения** (сайдбар, chrome://extensions) задаётся в манифесте:

- `packages/browseros-agent/apps/agent/wxt.config.ts` → `manifest.action.default_icon`: `icon/16.png`, `icon/32.png`, `icon/48.png`, `icon/128.png`.

Эти файлы лежат в сборке расширения (часто в `packages/browseros-agent/apps/agent/` или в сгенерированной папке типа `public/icon/`). Нужно подложить туда PNG PonyClaw (16, 32, 48, 128). Можно взять из `packages/browseros/resources/icons/` после шага 2:

```bash
cp packages/browseros/resources/icons/product_logo_16.png  packages/browseros-agent/apps/agent/icon/16.png
cp packages/browseros/resources/icons/product_logo_32.png packages/browseros-agent/apps/agent/icon/32.png
cp packages/browseros/resources/icons/product_logo_48.png packages/browseros-agent/apps/agent/icon/48.png
cp packages/browseros/resources/icons/product_logo_128.png packages/browseros-agent/apps/agent/icon/128.png
```

(в wxt.config.ts указано `icon/16.png` и т.д.; папку `icon/` в agent может создавать сборка или её нужно создать и положить туда PNG).

---

## Кратко

1. Заменить **app_icon.png** и **static/*.svg** на PonyClaw.
2. Запустить **generate_icons.py**.
3. Убедиться, что **copy_resources** скопировал иконки в Chromium (или скопировать вручную, включая **chromium/linux/product_logo_16.png**).
4. **Пересобрать** браузер.
5. Для расширения — подложить **icon/16,32,48,128.png** из resources/icons и пересобрать расширение.

После этого новый логотип будет везде: окно, тулбар (кнопка Pony), настройки, расширение.
