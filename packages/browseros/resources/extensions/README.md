# Локальные bundled-расширения (опционально)

По умолчанию сборка браузера **скачивает** расширения (Agent, Controller, Bug Reporter) с CDN. Чтобы использовать **свои** .crx (например с брендингом PonyAI и своими логотипами):

1. Положите в этот каталог:
   - **`bundled_extensions.json`** — список расширений в формате:
     ```json
     {
       "bflpfmnmnokmjhmgnolecpppdbdophmk": {
         "external_crx": "bflpfmnmnokmjhmgnolecpppdbdophmk.crx",
         "external_version": "1.0.0"
       },
       ...
     }
     ```
   - Файлы **`<extension_id>.crx`** для каждого расширения (например `bflpfmnmnokmjhmgnolecpppdbdophmk.crx` для Agent V2). Пример JSON — **`bundled_extensions.json.example`** (скопируйте в `bundled_extensions.json` и при необходимости поменяйте ID/имя файла).

2. При наличии здесь хотя бы одного .crx и `bundled_extensions.json` сборка **не будет качать** расширения с CDN и скопирует файлы из этого каталога в дерево Chromium.

Исходники расширения (Agent UI, popup «Assistant») — в репозитории [BrowserOS-agent](https://github.com/browseros-ai/BrowserOS-agent), приложение `apps/agent`.

**Сборка расширения с брендингом PonyAI (из корня репо ai_browser):**
```bash
./scripts/build_ponyai_extension.sh
```
Скрипт клонирует BrowserOS-agent (или использует `BROWSEROS_AGENT_DIR`), применяет ребренд (PonyAI + иконки из `packages/browseros/resources/icons`), собирает расширение и копирует его в `resources/extensions/agent-build/`. Дальше: загрузить как «Load unpacked» из `agent-build/` или упаковать в .crx из консоли: `./scripts/pack_agent_crx.sh` (из корня репо; при наличии `agent.pem` здесь — получится `bflpfmnmnokmjhmgnolecpppdbdophmk.crx`), либо через Chrome → Extensions → Pack extension.

Подробнее — в [docs/REBRANDING.md](../../../docs/REBRANDING.md) (раздел 1.8 Chrome-расширение).
