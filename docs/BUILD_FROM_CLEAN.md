# Полная пересборка с нуля (после отката на main до мерджа)

Используй, когда нужно почистить Chromium и заново прогнать setup + prep + build. Версия Chromium: **142.0.7444.49** (см. `packages/browseros/CHROMIUM_VERSION`).

## 1. Почистить Chromium src (чтобы gclient не ругался на uncommitted changes)

```bash
cd /lambda/nfs/knx-west/aib/chromium/src
git reset --hard refs/tags/142.0.7444.49
git clean -fdx
cd /lambda/nfs/knx-west/aib/chromium
```

## 2. Синхронизировать зависимости Chromium

```bash
cd /lambda/nfs/knx-west/aib/chromium
gclient sync -D --no-history --revision=src@refs/tags/142.0.7444.49
```

## 3. Полная сборка BrowserOS (setup + prep + build)

```bash
cd /home/ubuntu/knx-west/aib/ai_browser/packages/browseros
uv sync
uv run browseros build \
  --chromium-src /lambda/nfs/knx-west/aib/chromium/src \
  --setup \
  --prep \
  --build \
  --build-type debug \
  2>&1 | tee ../../browser-build.log
echo "Done at $(date). Check browser-build.log"
```

Если репо под NFS по пути `/lambda/nfs/knx-west/aib/ai_browser`, замени `cd` на:

```bash
cd /lambda/nfs/knx-west/aib/ai_browser/packages/browseros
```

и в `tee` оставь `../../browser-build.log` (лог в корне ai_browser).

## 4. Запуск браузера после сборки

```bash
/lambda/nfs/knx-west/aib/chromium/src/out/Default_x64/browseros \
  --enable-logging=stderr \
  --user-data-dir=/tmp/test-profile
```

## Расширение (PonyAI)

На ветке `main` (37419c9) в репо уже есть скрипты сборки расширения. Если нужен билд с новыми иконками/именами:

1. Собрать расширение: `./scripts/build_ponyai_extension.sh` (из корня ai_browser).
2. Упаковать в .crx: `./scripts/pack_agent_crx.sh`.
3. При необходимости обновить ID и `bundled_extensions.json` (см. docs/EXTENSION_PONYAI_BUILD.md).

Если расширение уже собрано и лежит в `packages/browseros/resources/extensions/` (agent-build и/или .crx + bundled_extensions.json), шаг prep при сборке браузера подхватит их автоматически.
