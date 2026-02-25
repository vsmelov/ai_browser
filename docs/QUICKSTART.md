# Рабочая инструкция по сборке (от нуля до запуска)

Пошаговая инструкция: зависимости, сборка browseros_server, сборка браузера, запуск. Подробности — в [BUILD.md](BUILD.md).

---

## Что нужно заранее

- **Сервер/ПК:** Linux (Ubuntu 22.04 или аналог), ~100 GB свободного места, достаточно RAM для сборки Chromium.
- **Инструменты:** git, Python 3, [depot_tools](https://chromium.googlesource.com/chromium/tools/depot_tools.git) (для Chromium), [Bun](https://bun.sh) (для сборки сервера), [UV](https://astral.sh/uv) (для сборки браузера).

---

## Шаг 1. Репозиторий и Chromium

### 1.1 Клонировать репозиторий

```bash
git clone <ваш-форк-или-upstream> ai_browser
cd ai_browser
```

### 1.2 Установить depot_tools и получить Chromium

```bash
# Установить depot_tools (один раз)
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$PWD/depot_tools:$PATH"

# Получить Chromium (долго, ~100 GB)
mkdir -p chromium && cd chromium
fetch --no-history chromium
cd ..
```

Путь к исходникам Chromium: `chromium/src`. Версия задаётся в `packages/browseros/CHROMIUM_VERSION` (сейчас **142.0.7444.49**).

### 1.3 Проверить тег в Chromium

```bash
cd chromium/src
git fetch origin refs/tags/142.0.7444.49:refs/tags/142.0.7444.49 --no-tags
git tag -l "142.0.7444.49"
# Должен вывести: 142.0.7444.49
cd ../..
```

---

## Шаг 2. Бинарник browseros_server (MCP/CDP-сервер)

Без этого бинарника браузер соберётся, но MCP/CDP-сервер не будет работать. Собираем из исходников (R2 у BrowserOS приватный).

```bash
# Из корня репозитория ai_browser
./scripts/build_browseros_server.sh
```

Нужны **Bun** и **git**. Скрипт клонирует [BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent) в `.cache/BrowserOS-agent`, собирает бинарник и кладёт его в `packages/browseros/resources/binaries/browseros_server/`. Подробнее — [BROWSEROS_SERVER.md](BROWSEROS_SERVER.md).

---

## Шаг 3. Сборка браузера

### 3.1 UV и зависимости

```bash
cd ai_browser/packages/browseros
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"   # или путь, куда установился uv
uv sync
```

### 3.2 Первая сборка (setup + prep + build)

Подставьте свой путь к **chromium/src** (каталог с исходниками Chromium).

```bash
uv run browseros build \
  --chromium-src /path/to/chromium/src \
  --setup --prep --build --build-type debug
```

- **--setup** — очистка дерева Chromium, checkout тега из `CHROMIUM_VERSION`, `gclient sync`. Делать один раз (или после смены версии).
- **--prep** — патчи, копирование ресурсов (в т.ч. browseros_server), иконки, configure.
- **--build** — gn + ninja.

Сборка может занять 1–3 часа.

Если патчи падают (`does not exist in index`, `patch does not apply`) — дерево в смешанном состоянии. Запустите ещё раз с **--setup --prep --build** (один раз полный цикл). Подробнее — [BUILD.md](BUILD.md#browseros-server-бинарник-и-r2).

### 3.3 Следующие сборки (только компиляция)

```bash
uv run browseros build \
  --chromium-src /path/to/chromium/src \
  --prep --build --build-type debug
```

Или только пересборка без повторного prep:

```bash
uv run browseros build \
  --chromium-src /path/to/chromium/src \
  --build --build-type debug
```

---

## Шаг 4. Запуск браузера

Бинарник (Linux x64 debug):

```bash
/path/to/chromium/src/out/Default_x64/browseros \
  --enable-logging=stderr --user-data-dir=/tmp/browseros-profile
```

Пример для типичной раскладки:

```bash
~/chromium/src/out/Default_x64/browseros \
  --enable-logging=stderr --user-data-dir=/tmp/browseros-profile
```

При ошибках про sandbox в тестовой среде можно добавить `--no-sandbox` (только для отладки).

---

## Шаг 5. Удалённый рабочий стол (опционально)

Если собираете на сервере и хотите потыкать браузер в GUI:

- Установка Xfce + xrdp: см. [REMOTE_DESKTOP.md](REMOTE_DESKTOP.md).
- Подключение по RDP: IP сервера, порт 3389, логин/пароль — пользователь Linux.
- В облаке (AWS и т.п.) нужно открыть порт **3389** в Security Group / файрволе.

---

## Краткий чеклист

| Шаг | Действие |
|-----|----------|
| 1 | Клонировать ai_browser, установить depot_tools, `fetch chromium`, проверить тег в `chromium/src` |
| 2 | Запустить `./scripts/build_browseros_server.sh` из корня ai_browser |
| 3 | В `packages/browseros`: `uv sync`, затем `uv run browseros build --chromium-src <path> --setup --prep --build --build-type debug` |
| 4 | Запустить `<chromium-src>/out/Default_x64/browseros --enable-logging=stderr --user-data-dir=/tmp/browseros-profile` |
| 5 | (Опционально) Настроить RDP по [REMOTE_DESKTOP.md](REMOTE_DESKTOP.md) |

Подробности по каждому шагу, R2, заглушкам и конфигам — в [BUILD.md](BUILD.md).
