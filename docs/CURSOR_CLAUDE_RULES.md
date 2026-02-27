# Куда класть инструкции для Cursor и Claude AI

Краткая справка по стандартным местам, откуда Cursor IDE и Claude читают правила и подсказки по проекту.

## Cursor IDE

**Рекомендуемый способ (актуальный):**

- **`.cursor/rules/`** — папка с файлами правил. Форматы:
  - **`.md`** — обычный markdown, без метаданных.
  - **`.mdc`** — markdown с frontmatter, чтобы задать, когда правило применяется:

    ```yaml
    ---
    description: Описание правила
    globs: ["src/components/**/*.tsx"]   # только для этих файлов
    alwaysApply: true                    # или: применять в каждом чате
    ---
    Текст правила...
    ```

  Файлы можно раскладывать по подпапкам (например `.cursor/rules/frontend/`, `.cursor/rules/build/`).

**Устаревшие, но ещё работают:**

- **`.cursorrules`** — один файл в корне проекта (старый формат).
- **`AGENTS.md`** — один markdown-файл в корне, без frontmatter.

**Порядок приоритета** (если задано несколько источников):

1. Team Rules (планы Cursor Team/Enterprise)
2. Project Rules (`.cursor/rules/`)
3. User Rules (настройки Cursor у пользователя)
4. Legacy: `.cursorrules`
5. `AGENTS.md`

**Режимы применения правил** (в .mdc через frontmatter):

- **Always Apply** — в каждой сессии.
- **Apply Intelligently** — когда модель считает правило уместным.
- **Apply to Specific Files** — по glob-паттернам (например только для `*.tsx`).
- **Apply Manually** — когда правило явно вызывают через @ в чате.

Рекомендации: правила держать короткими (до ~500 строк), выносить общие вещи в отдельные файлы и коммитить в git, чтобы команда использовала одни и те же инструкции.

## Этот репозиторий

- **`CLAUDE.md`** в корне — используется как **Project Instructions** в Cursor (workspace rules). Сюда кладут общие указания по проекту, которые должны видеть AI-ассистенты.
- Папки **`.cursor/rules/`** в репо пока нет — при необходимости можно создать и добавить туда правила (например отдельный файл про сборку расширения или про стиль кода).

## Полезные ссылки

- [Cursor Docs — Rules](https://cursor.com/docs/context/rules)
- [Cursor Rules Guide (design.dev)](https://design.dev/guides/cursor-rules/)
