# Подтягивание upstream (browseros-ai/BrowserOS) и проверка

## Текущий прогресс (закоммитить)

- Фиксы сборки: nxtscape_first_run.h (raw string delimiter, #endif), bundled extension loader (TryLoadFromBundled), версия extension 0.0.52 в JSON.
- Документация и codegen: fallback на schema/schema.graphql (совместимость с BrowserOS-agent PR #364).
- Build: write_bundled_build_gn.py, clean.py, bundled_extensions.

## Шаг 1: Закоммитить прогресс

```bash
cd /home/ubuntu/knx-west/aib/ai_browser

git add \
  .gitignore \
  docs/EXTENSION_PONYAI_BUILD.md \
  docs/REBRANDING.md \
  packages/browseros/build/cli/build.py \
  packages/browseros/build/config/debug.linux.yaml \
  packages/browseros/build/modules/extensions/__init__.py \
  packages/browseros/build/modules/extensions/bundled_extensions.py \
  packages/browseros/build/modules/extensions/write_bundled_build_gn.py \
  packages/browseros/build/modules/setup/clean.py \
  packages/browseros/chromium_patches/chrome/browser/browseros/bundled_extensions/BUILD.gn \
  packages/browseros/chromium_patches/chrome/browser/browseros/extensions/browseros_extension_installer.cc \
  packages/browseros/chromium_patches/chrome/browser/ui/webui/nxtscape_first_run.h \
  packages/browseros/resources/extensions/bundled_extensions.json \
  scripts/agent-codegen.ts \
  scripts/build_ponyai_extension.sh

# Опционально: build_resources_only.sh, docs/SYNC_UPSTREAM.md
git add docs/SYNC_UPSTREAM.md scripts/build_resources_only.sh 2>/dev/null || true

git status
git commit -m "fix: first-run build, bundled extensions loader, extension version 0.0.52; codegen fallback to schema/schema.graphql (PR #364)"
```

Не коммитить: `extension-build.log`, `new_logos/`, бинарник `browseros_server/` (уже в .gitignore).

## Шаг 2: Добавить upstream и влить их main

Цель: получить код из browseros-ai/BrowserOS (их main) в свою ветку, не теряя свои коммиты. Делаем merge их main в нашу ветку.

```bash
cd /home/ubuntu/knx-west/aib/ai_browser

# Один раз добавить upstream (репо браузера, не agent)
git remote add upstream https://github.com/browseros-ai/BrowserOS.git 2>/dev/null || true
git fetch upstream

# Влить их main в текущую ветку (появится merge-коммит или конфликты)
git merge upstream/main -m "Merge upstream/main (sync with browseros-ai/BrowserOS)"
```

Если будут конфликты — разрешить, затем:

```bash
git add .
git commit --no-edit
```

## Шаг 3: Проверить CHROMIUM_VERSION

После merge убедиться, что версия Chromium не поменялась (чтобы не ломать текущую сборку):

```bash
cat packages/browseros/CHROMIUM_VERSION
```

Ожидаем: `MAJOR=142`, `MINOR=0`, `BUILD=7444`, `PATCH=49`. Если upstream изменил файл — либо откатить только этот файл к нашей версии, либо обновить под их тег и пересобрать Chromium.

Откат только CHROMIUM_VERSION к нашему значению (если upstream его поменял):

```bash
git checkout HEAD -- packages/browseros/CHROMIUM_VERSION
# или явно восстановить содержимое и закоммитить
```

## Шаг 4: Сборка (вручную)

После merge и проверки версии — как обычно:

- `--prep` в свой chromium tree (если нужно переприменить патчи).
- Сборка chrome/chromedriver (ты запускаешь вручную).

## Шаг 5: Extension и GraphQL (их правка PR #364)

Их фикс (bundled schema) живёт в репо **BrowserOS-agent**, не в BrowserOS (браузер).

- При сборке расширения скрипт клонирует/пуллит `https://github.com/browseros-ai/BrowserOS-agent.git` в `.cache/BrowserOS-agent`. Чтобы точно подтянуть их main с PR #364:
  - либо удалить кэш и собрать заново: `rm -rf .cache/BrowserOS-agent`, затем `./scripts/build_ponyai_extension.sh`;
  - либо зайти в кэш и пулл: `cd .cache/BrowserOS-agent && git fetch origin && git checkout main && git pull`.
- У нас в репо уже есть fallback в `scripts/agent-codegen.ts` (schema/schema.graphql), так что даже со старым клоном agent сборка может пройти, если в агенте есть `apps/agent/schema/schema.graphql` (после их PR #364).

## Итог

1. Закоммитили прогресс.
2. Добавили upstream, влили `upstream/main` в свою ветку.
3. Проверили `CHROMIUM_VERSION`, при необходимости откатили.
4. Собрали браузер вручную.
5. При следующей сборке extension — свежий клон agent даст их код с PR #364 (без костыля с GraphQL).

Ребрендинг (логотипы, строки PonyAI и т.д.) — отдельным следующим шагом.
