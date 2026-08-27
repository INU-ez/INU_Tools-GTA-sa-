# Release Notes — v2.3.1

Bugfix / follow-up release on top of 2.3.0. Ready-to-paste text for the GitHub
release page and the extensions.blender.org version notes. Copy the language you
need.

---

## 🇬🇧 English

```markdown
## ✨ Added

- **Ariane "Create model" — options.** **"Auto-LOD from main model"** — when a model has no `_LOD` mesh, a copy of the main model is sent as the distant LOD (turn off for models with no LOD). **"Empty COL when none"** — ON attaches an empty bounding-box collision; OFF builds the collision from the main model's geometry.
- **Auto-generated LOD/COL now land in the Blender scene.** The auto LOD/COL are also created as editable `<name>_LOD` / `<name>_COL` objects (tagged with their Ariane names) so you can edit them, and a re-export updates them.
- **Model ID from Ariane.** The ID Ariane allocates to a newly created model is written back to the object's Model ID (when Ariane reports it).

## 🔧 Changed

- **Ariane "Create model" groups selected meshes by base name.** `name_DFF` / `name_LOD` / `name_COL` are now treated as ONE model "name" with its LOD and COL, instead of each selected mesh becoming a separate model with false "no COL / no LOD" warnings.
- **Ariane bridge:** the "Auto" import button is renamed **"Sync import"**.
- **Targeted classification cache.** The model-type cache is now invalidated only for the objects that actually changed, not cleared wholesale on every depsgraph update — so the N-panel no longer re-scans every object's materials on each scene change. (The material-browser thumbnail lag itself is Blender's own preview generation.)

## 🐛 Fixed

- **Re-exporting an Ariane model now updates its LOD.** The auto-created LOD is tagged with its Ariane name, so "Export → Ariane" finds and refreshes it — previously the LOD stayed stuck at its creation state.
- **In-addon "What's New" popup** now lists the current 2.3.x highlights (it still showed an old feature list).
- **Manifest:** dropped `SPDX:OFL-1.1` from the license list — it isn't accepted by extensions.blender.org (the bundled Inter font keeps its OFL license as `data/fonts/OFL.txt`).
- Removed an orphaned test that referenced a deleted module.
```

---

## 🇷🇺 Русский

```markdown
## ✨ Добавлено

- **Диалог «Ariane: создать модель» — опции.** **«Авто-LOD из основной модели»** — если у модели нет `_LOD`-меша, копия основной уходит как дальний LOD (выключи для моделей без LOD). **«Пустая COL если нет своей»** — ВКЛ приложит пустую габаритную коллизию; ВЫКЛ построит COL из геометрии основной модели.
- **Авто-LOD/COL теперь создаются и в сцене.** Авто LOD/COL появляются редактируемыми объектами `<имя>_LOD` / `<имя>_COL` (с ariane-тегами), чтобы их можно было править, а повторный экспорт их обновлял.
- **Model ID из Ariane.** ID, который Ariane выделяет созданной модели, пишется в Model ID объекта (если Ariane его сообщает).

## 🔧 Изменено

- **«Создать модель» группирует выделенные меши по базовому имени.** `имя_DFF` / `имя_LOD` / `имя_COL` теперь одна модель «имя» с её LOD и COL, а не три отдельные с ложными «нет COL / нет LOD».
- **Мост Ariane:** кнопка импорта «Авто» переименована в **«Sync импорт»**.
- **Точечная инвалидация кэша классификации.** Кэш типа модели чистится только у реально изменившихся объектов, а не целиком на каждый depsgraph-апдейт — N-панель больше не пересканирует материалы всех объектов на каждое изменение сцены. (Сам лаг миниатюр в браузере материалов — это генерация превью самого Blender.)

## 🐛 Исправлено

- **Повторный экспорт модели в Ariane теперь обновляет её LOD.** Авто-LOD помечается ariane-именем, и «Экспорт → Ariane» его находит и обновляет — раньше LOD застревал в состоянии на момент создания.
- **Встроенный поп-ап «What's New»** теперь показывает актуальные фичи 2.3.x (раньше был старый список).
- **Манифест:** убран `SPDX:OFL-1.1` из списка лицензий — extensions.blender.org его не принимает (лицензия шрифта Inter осталась файлом `data/fonts/OFL.txt`).
- Удалён осиротевший тест, ссылавшийся на удалённый модуль.
```

---

## 🇪🇸 Español (resumen)

```markdown
## v2.3.1

- ✨ **«Crear modelo» de Ariane — opciones:** «Auto-LOD del modelo principal» (sin `_LOD` → se envía una copia del principal como LOD lejano) y «COL vacío si no hay» (ON — colisión vacía de caja envolvente; OFF — colisión desde la geometría del principal).
- ✨ **Los LOD/COL automáticos ahora se crean en la escena** como objetos editables `<nombre>_LOD` / `<nombre>_COL` (etiquetados) para poder editarlos y que la re-exportación los actualice.
- ✨ **Model ID de Ariane** escrito de vuelta en el objeto.
- 🔧 **«Crear modelo» agrupa por nombre base:** `nombre_DFF/_LOD/_COL` = un modelo, no tres separados. Botón de importación «Auto» → **«Sync import»**. Invalidación puntual de la caché de clasificación (la N-panel ya no reescanea todos los materiales en cada cambio de escena).
- 🐛 La re-exportación a Ariane ahora actualiza el LOD (se etiqueta con su nombre de Ariane). Manifiesto: se quitó `SPDX:OFL-1.1` (no aceptado por extensions.blender.org). Eliminado un test huérfano.
```
