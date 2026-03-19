# Расследование: почему 13 патчей не применяются к тегу 145.0.7632.45

Проверка: берём чистый файл с тега `145.0.7632.45`, накатываем наш патч (`git apply -p1`), сравниваем с деревом. Для 13 файлов `git apply` падает — ниже причины по каждому.

---

## 1. `chrome/browser/browseros/server/browseros_server_manager.cc`

**Ошибка:** `error: corrupt patch at line 1077`

**Причина:** В заголовке хука указано `+1,1072` (добавить 1072 строки), а в файле патча строк с префиксом `+` всего **1071**. Не хватает одной строки — парсер `git apply` доходит до конца хука и фиксирует «corrupt» (ожидалась ещё одна строка контента).

**Вывод:** Ошибка в самом патче (неверное число в `@@ -0,0 +1,1072 @@` или лишняя/недостающая строка в теле).

---

## 2. `chrome/BUILD.gn`

**Ошибка:** `patch failed: chrome/BUILD.gn:369`

**Причина:** Патч ожидает контекст вокруг строки 369:
```gn
data_deps += [
  "//chrome/browser/resources/media/mei_preload:component",
  "//components/privacy_sandbox/...",
```
В дереве на теге 145.0.7632.45 между `mei_preload` и `privacy_sandbox` уже есть ещё одна запись: `"//chrome/browser/web_applications/isolated_web_apps/key_distribution/preload:component"`. Список `data_deps` изменился — контекст не совпадает.

**Вывод:** Патч снят с более старой ревизии; в 145.0.7632.45 блок переставлен/дополнен.

---

## 3. `chrome/browser/BUILD.gn`

**Ошибка:** `patch failed: chrome/browser/BUILD.gn:1901`

**Причина:** Патч вставляет `"//chrome/browser/browseros"` после `"//chrome/browser/breadcrumbs"` и перед `"//chrome/browser/browsing_data:constants"`. На теге 145.0.7632.45 блок `breadcrumbs` / `browsing_data:constants` находится около **строки 1815**, а не 1901. Нумерация сдвинулась (~86 строк).

**Вывод:** В новой версии BUILD.gn изменилась структура/порядок deps — патч привязан к старым номерам строк.

---

## 4. `chrome/browser/about_flags.cc`

**Ошибка:** `patch failed: chrome/browser/about_flags.cc:12068`

**Причина:** Патч вставляет флаги BrowserOS после `bookmarks-tree-view` и ожидает сразу после вставки контекст `#endif` и затем `{"enable-secure-payment-confirmation-availability-api"...}`. На теге после `bookmarks-tree-view` идёт `#endif`, затем `#if BUILDFLAG(IS_ANDROID)` и `new-etc1-encoder`, а не `enable-secure-payment-confirmation...`. Порядок флагов и блоков `#if` изменился.

**Вывод:** Структура `kFeatureEntries` в 145.0.7632.45 другая — другой порядок/набор флагов, контекст хука не совпадает.

---

## 5. `chrome/browser/buildflags.gni`

**Ошибка:** `patch failed: chrome/browser/buildflags.gni:12`

**Причина:** Патч ожидает строку 12:
```gni
enable_updater = is_chrome_branded
```
На теге там:
```gni
enable_updater = is_chrome_branded && !is_fuchsia && target_os != "android"
```
Условие для `enable_updater` расширено — одна строка заменена на другую, контекст не совпадает.

**Вывод:** Патч снят с версии, где не было условий по fuchsia/android.

---

## 6. `chrome/browser/prefs/browser_prefs.cc`

**Ошибка:** `patch failed: chrome/browser/prefs/browser_prefs.cc:24`

**Причина:** Патч вставляет include’ы после `#include "chrome/browser/browser_process_impl.h"` (строка 24). В чистом файле на теге на строке 24 уже другой include (например `prefers_default_scrollbar_styles_prefs.h`), а `browser_process_impl.h` — на 25; выше есть дополнительный include (`actor_ui_state_manager_prefs.h` в нашей базе или аналог). Набор/порядок include’ов в начале файла изменился.

**Вывод:** Сдвиг нумерации и контекста из-за изменений в верхе файла.

---

## 7–13. Остальные файлы

Для всех остальных сообщение однотипное: `patch failed: <file>:<line>`.

- **chrome/browser/global_keyboard_shortcuts_mac.mm:166**  
  Контекст вокруг 166-й строки на теге не совпадает с контекстом в патче (другая раскладка шорткатов или блоков).

- **chrome/browser/importer/external_process_importer_client.cc:14**  
  Начало файла (include’ы или первые вызовы) изменилось, контекст хука не найден.

- **chrome/browser/metrics/chrome_metrics_service_client.cc:76**  
  Блок инициализации/регистрации метрик сдвинут или переписан.

- **chrome/browser/ui/browser_command_controller.cc:70**  
  Порядок/набор команд или блоков в контроллере изменился.

- **chrome/browser/ui/extensions/extension_side_panel_utils.h:63**  
  Сигнатуры или блок кода около 63-й строки на теге не совпадают с ожидаемым контекстом.

- **chrome/browser/ui/toolbar/toolbar_actions_model.cc:323**  
  Дополнительно в логе есть предупреждения про trailing whitespace в самом патче; контекст вокруг 323 не совпадает (модель тулбара менялась).

- **chrome/browser/ui/views/toolbar/pinned_action_toolbar_button.cc:8**  
  Аналогично: trailing whitespace в патче; контекст в начале файла (или около 8-й строки) на теге другой.

**Общий вывод по 7–13:** Патчи сняты с другой ревизии Chromium; в 145.0.7632.45 соответствующие файлы изменились (добавлены/удалены строки, переставлены блоки), поэтому номера строк и окружающий контекст не совпадают с тем, что записано в патчах.

---

## Расследование по git: почему пять патчей не совпадают с тегом 145.0.7632.45

### Что сделано

- Исправлен **только** патч `browseros_server_manager.cc`: в заголовке хука было `+1,1072`, в теле 1071 строка с `+` — заменено на `+1,1071`.
- Для пяти патчей (chrome/BUILD.gn, chrome/browser/BUILD.gn, about_flags.cc, buildflags.gni, browser_prefs.cc) правки **не вносились** — только разобрана история.

### Результат разбора истории

1. **Коммит 81a16bb «feat: chromium 145 upgrade (#362)»**  
   В нём обновлены CHROMIUM_VERSION и много других файлов в `chromium_patches/`, но **ни один из этих пяти патчей не трогался**:
   - в `git show 81a16bb --stat` нет ни `chrome/BUILD.gn`, ни `chrome/browser/BUILD.gn`, ни `about_flags.cc`, ни `buildflags.gni`, ни `browser_prefs.cc`.

2. **Последние изменения по каждому из пяти патчей** (до текущего состояния репо):
   - `chrome/BUILD.gn` — **acdd1fe** (improve extension installer + updater #278)
   - `chrome/browser/BUILD.gn` — **50a797a** (fix: sparkle build flag #260)
   - `chrome/browser/about_flags.cc` — **4898472** (keyboard shortcut for llm chat/hub)
   - `chrome/browser/buildflags.gni` — **f88a62b** (mac sparkle fixes #258)
   - `chrome/browser/prefs/browser_prefs.cc` — **bd1cd19** (new browseros prefs, toolbar pin/unpin)

   Все эти коммиты **раньше** 81a16bb (145 upgrade). То есть при переходе на 145 эти пять файлов патчей не перегенерировали и не подстраивали под новую базу.

3. **Содержимое при 142 и 145**  
   - В **0b04473** (chromium 142 upgrade) в `chrome/BUILD.gn` контекст вокруг строки 369 ещё без записи `isolated_web_apps/key_distribution/preload`; в **81a16bb** в том же патче уже два новых пункта (bundled_extensions + server resources), но номера строк и контекст остались от старой базы (369, 1197 и т.д.).  
   - В актуальном дереве на теге **145.0.7632.45** в chrome/BUILD.gn между mei_preload и privacy_sandbox уже есть эта запись, а блок breadcrumbs в chrome/browser/BUILD.gn сдвинут (около 1815 вместо 1901).  
   - То есть патчи для этих файлов по сути остались от **142 или раннего 145**, а не от текущего тега 145.0.7632.45.

### Вывод по расследованию

- При переходе 142 → 145 в коммите 81a16bb **эти пять патчей не обновляли**. Их содержимое и контекст по-прежнему соответствуют более старой ревизии Chromium (142 или ранний 145).
- Текущий тег **145.0.7632.45** в этих местах уже другой (другие строки, порядок deps/flags/includes), поэтому при накатке на «чистое» дерево с тега патч не ложится.
- Ваша фраза «мы сами всё сломали, потом починили без замены патчей» хорошо стыкуется с этим: по факту могли поправить **дерево Chromium** (ручные правки или `apply --3way`), а **файлы патчей в репозитории так и остались** под старую базу. То есть «что пошло не так» — не обновили эти пять патчей при 145 upgrade; они не перегенерированы под 145.0.7632.45.
- Чтобы они снова гарантированно накатывались на чистый 145.0.7632.45, нужно **переснять или вручную подогнать эти пять патчей** под актуальное содержимое файлов на теге (обновить контекст и номера строк). Сами патчи я по вашей просьбе не правил.

---

## Сводка

| Тип причины | Файлы |
|-------------|--------|
| Ошибка в самом патче (hunk size / corrupt) | `browseros_server_manager.cc` |
| Изменился список/порядок (deps, includes, flags) | `chrome/BUILD.gn`, `chrome/browser/BUILD.gn`, `about_flags.cc`, `buildflags.gni`, `browser_prefs.cc` |
| Сдвиг нумерации и контекста в большом файле | остальные 7 файлов |

Ни один из случаев не говорит о том, что текущее дерево «неправильное» — оно может быть вручную приведено в соответствие с нашими правками или накатано через `git apply --3way`. Скрипт не может построить эталон только потому, что патч не применяется к **чистому** файлу с тега 145.0.7632.45.
