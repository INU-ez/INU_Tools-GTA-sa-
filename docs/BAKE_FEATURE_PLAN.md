# INU Tools — Запекание карт и композит в одну текстуру (Texture Bake & Composite)

> Архитектурный план фичи. Сгенерирован многоагентным анализом (глубокое чтение TexTools + INU Tools → 3 конкурирующих архитектуры → судейство → синтез → состязательная критика).
> Статус: **APPROVE WITH REQUIRED FIXES** — архитектура утверждена, но §0 содержит блокирующие правки, которые нужно учесть ДО реализации.

## Статус реализации (обновляется по ходу)

| Этап | Что | Статус | Проверка (headless Blender 5.1) |
|---|---|---|---|
| M1 | `bake_core` (движок + BakeStateGuard + numpy I/O) | ✅ Готово | 14/14 |
| M2 | `bake_maps`: AO, Diffuse (albedo), Bevel | ✅ Готово | 10/10 |
| M3 | Shadow + Diffuse-Lit (самодостаточный свет + изоляция) | ✅ Готово | 17/17 |
| M4 | `bake_composite` (numpy layer-stack, blend, sRGB) | ✅ Готово | 9/9 (чистый numpy) |
| M5 | scene_settings + операторы | ✅ Готово | — |
| M6 | UI (панель + UIList + registry + profiles) | ✅ Готово | полная интеграция 24/24 |
| M7 | полировка + валидация на реальных DFF | ⏳ Позже | — |
| M8 | раскрытие contrast/gamma/influence + TXD-экспорт | ⏳ Позже | contrast/gamma уже работают |
| **M9a** | **Transfer UV→UV** (печь в чистую UV; исходные текстуры пинятся к source `active_render` UV — иначе каша) | ✅ Готово | 6/6 + 4/4 transfer |
| **M9b** | **Transfer hi→low** (детект пары по настраиваемым _hi/_low + selected-to-active + cage) | ✅ Готово | 7/7 |

**Реализованные карты:** AO, Diffuse (albedo), Diffuse-Lit, Shadow, Bevel + композит (5 blend-режимов, opacity, per-layer контраст/гамма, sRGB через color management Blender, сохранение alpha базы).

**Отступления от плана (обоснованные):**
- Свет-риг — на **SUN-лампах** (а не POINT-8 как в §5): нет inverse-square falloff → экспозиция инвариантна к размеру объекта (закрывает C5 чище). Своя коллекция `INU_Bake_Lights`, не `Prelight_Lights` (C3).
- Изоляция чужого света — через `hide_render` всех прочих объектов (убирает и чужие лампы, И эмиссивные материалы — C2) + нейтральный мир, всё восстанавливается.
- Bevel — **плоский материал** (ShaderNodeMath), а не node-группа: MapRange имеет дублированные сокеты (ловушка как у ShaderNodeMix), Math-узел надёжнее. `compat.node_group_*` зарезервирован.
- Оператор перед запеканием снимает выделение со всех кроме цели (иначе bake падает на скрытом выделенном объекте).

**Решение по M9 (transfer), зафиксировано 2026-06-03:** делать ОБА режима из TexTools — **hi→low** (объект→объект, `use_selected_to_active` + cage, авто-пары по **настраиваемым** суффиксам + `_cage`) и **UV→UV** (одна развёртка → другая на том же меше). Суффиксы — поля в настройках (пользователь задаёт свои).

---

## 0. Критические правки из состязательного ревью (ОБЯЗАТЕЛЬНО учесть)

Эти пункты найдены на фазе критики уже ПОСЛЕ синтеза основного плана (§1–§11). Они не отменяют архитектуру, но без них фича будет «работать, но неправильно».

| # | Серьёзность | Проблема | Правка |
|---|---|---|---|
| **C1** | 🔴 HIGH | **Цветовое пространство не учтено.** Пиксели Blender — scene-linear float; текстуры GTA SA — sRGB 8-bit. Если композитить в linear и писать как есть, в игре текстура будет тёмной/неправильной. Это ровно твой вопрос «слить корректно». | Композитим в linear, затем **перед записью** финала кодируем RGB в sRGB (`c<=0.0031308 ? 12.92*c : 1.055*c^(1/2.4)-0.055`), **alpha не трогаем**. Либо выставляем `image.colorspace_settings`. Юнит-тест: серый 0.5 round-trip. |
| **C2** | 🟠 MED | **Изоляция света неполная.** `hide_render` чужих ламп не убирает **эмиссивные материалы** других объектов — они протекают в `DIFFUSE_LIT` через indirect pass (неон/экраны/лава в SA-сценах). | Либо (a) на время light-прохода `hide_render=True` ВСЕМ объектам кроме target+риг (снапшот/восстановление), либо (b) для `DIFFUSE_LIT` ставить `use_pass_indirect=False` (проще, детерминированнее, лучше под «just works»). |
| **C3** | 🟠 MED | **Коллизия с prelight-коллекцией.** Переиспользование `prelight.create_prelight_scene_lights` тянет teardown `remove_prelight_scene_lights()`, который удаляет коллекцию с именем `'Prelight_Lights'` — а у юзера такая может быть от вершинного prelight. Bake снесёт её. | Bake использует ТОЛЬКО собственные имена коллекций (`INU_Bake_Prelight`, `INU_Bake_Lights`). Defensive sweep **не трогает** `Prelight_Lights`. Параметризовать имя коллекции в prelight-хелпере. |
| **C4** | 🟠 MED | **Cycles-guard ненадёжен.** `'cycles' in dir(scene)` — хрупкая эвристика; Cycles может быть **выключен** пользователем. | Проверять `'CYCLES' in [e.identifier for e in type(scene.render).bl_rna.properties['engine'].enum_items]`; иначе `report({'ERROR'}, T('Включите Cycles'))`. |
| **C5** | 🟠 MED | **Экспозиция DIFFUSE_LIT не масштаб-инвариантна.** POINT-лампы дают falloff 1/d², а дистанция рига ∝ размеру объекта → большие объекты темнее при том же `energy_scale`. | Масштабировать энергию на `distance²`, ЛИБО использовать `SUN` (без falloff) и для lit-diffuse, ЛИБО ambient через constant-world. Калибровать на объектах РАЗНОГО размера. |
| **C6** | 🟠 MED | **Bevel node-группа.** dot(BevelNormal, GeoNormal) НЕ лежит статически в [0,1] (отрицателен на вогнутостях, диапазон зависит от модели) → фикс. `MapRange 0..1` пересветит. Плюс сокет группы должен быть верного типа. | `MapRange` с осмысленным clamp и настраиваемыми From-Min/Max (или через `acos`); `node_group_new_output` создаёт `NodeSocketShader` для surface-выхода; `ShaderNodeBevel.samples` — свойство ноды, не вход. |
| **C7** | 🟡 LOW-MED | **Панель невидима под кастом-профилями.** `tools/profiles.py` показывает панель только если её idname в whitelist профиля. Новая `GTATOOLS_PT_bake_panel` не попадёт ни в один сохранённый профиль. | Добавить `('GTATOOLS_PT_bake_panel', '<label>')` в `ALL_TOGGLEABLE_PANELS`/`KNOWN_PANELS` в `tools/profiles.py`. |
| **C8** | 🟡 LOW | **`composite_layers` не «чистый numpy».** Заявлено «без bpy / headless-тест», но на вход подаётся `INUBakeLayer` (PropertyGroup, требует bpy) — противоречие. | Оператор (слой 4) извлекает из каждого `INUBakeLayer` обычный dataclass/tuple `(map_id, enabled, blend_mode, opacity, contrast, gamma, influence_target, influence_amount)` и передаёт ИХ. Тогда функция реально bpy-free. |
| **C9** | 🟡 LOW | **Скоуп `BakeStateGuard`.** Если per-map — engine/samples снапшотятся N раз (избыточно). | ОДИН guard вокруг всего прогона (engine/device/samples/target/denoising/world/hide_render — снапшот один раз); внутри per-map меняются только `bake.use_pass_*` + `bake_type`. |
| **C10** | ⚪ INFO | **Rig view-layer visibility.** Если коллекция рига `exclude=True` в активном view layer — лампы невидимы для bake → чёрный результат. | После создания рига найти его `LayerCollection` и форсить `exclude=False`/`hide_viewport=False`, снапшот/восстановление. |
| **C11** | ⚪ INFO | **Дрейф версии манифеста.** `blender_manifest.toml` = 2.0.2, а bl_info/коммиты = 2.0.3. Не вносится этим планом, но при бампе до 2.1.0 обновить ОБА. | Синхронизировать `blender_manifest.toml` и `bl_info`. |

> Примечание: рационал про migration-SKIP (§9 п.7) технически неточен (новые поля не итерируются старым load_post-хендлером), но действие безвредно. Оставить запись можно, формулировку «иначе упадёт» — убрать.

---

## 1. Обзор и философия

### Что строим
Подсистема, которая запекает несколько карт (**AO, Diffuse, Shadow, Bevel** + задел под «другие») через нативный **Cycles bake** и опционально **складывает любой их поднабор в одну финальную текстуру** numpy-композитором. Это «текстурный prelight»: тот же принцип, что уже есть в `tools/prelight.py` (запечь свет/затенение в данные модели, потому что движок GTA SA не имеет realtime-освещения и normal map), но результат пишется **в текстуру** (diffuse), а не в вершинные цвета. Для ванильной SA это и есть главный смысл — свет + окклюзия + износ кромок (bevel) запекаются прямо в diffuse, который движок умеет показывать.

### Архитектурная философия (синтез победителя + графты)
Берём **LAYERED SUBSYSTEM** как каркас (строгая однонаправленная слоистость, `BakeStateGuard` как context-manager, корректный Shadow через DIFFUSE-direct), и прививаем к нему:
- из **DATA-DRIVEN REGISTRY** — единую таблицу `BAKE_MAPS` (frozen `BakeMapDef`) как единственный источник правды + `_BLEND` как dict numpy-функций + `HAS_NODE_INTERFACE` compat-флаг + per-map дефолтные blend/opacity при добавлении слоя;
- из **PRAGMATIC** — добавление `gtatools_bake_layers` в migration-SKIP set, `poll()`-guard на доступность Cycles, `use_fake_user=False` для транзитных карт, выделенный **SUN-риг для Shadow** (8-точечный POINT-риг почти гасит тени).

### Почему опционально
Композит — **отдельная необязательная СТАДИЯ**, шлюзованная одним `BoolProperty gtatools_bake_composite_mode`:
- **OFF** → каждая включённая карта пишется в свою картинку `<output>_<map_id>` (обычный multi-map baker). Модуль `bake_composite` даже не импортируется в горячем пути.
- **ON** → те же запечённые numpy-слои складываются в одну текстуру `<output>`.

Переключатель меняет только финальную ветку записи, не путь запекания. Плюс per-map флаг `enabled` даёт «скомбинировать любой поднабор» — выключенные строки просто пропускаются в стеке.

---

## 2. Файловая / модульная архитектура

Строгое **однонаправленное** направление зависимостей (нижний слой никогда не импортирует верхний):

```
bake_composite (чистый numpy, НЕТ bpy)         ← unit-тестируется headless
        ▲
bake_core   (движок + BakeStateGuard; знает bake API, не знает INU-семантики)
        ▲
bake_maps   (BAKE_MAPS реестр; владеет светозависимостью + bevel node-группой)
        ▲
ops/bake_ops.py (операторы: оркестрация core+maps+composite, report(), undo)
        ▲
ui/panels.py + scene_settings.py (PropertyGroup'ы + GTATOOLS_PT_/UL_)
```

| Файл | Новый/Правка | Зона ответственности |
|---|---|---|
| `INU_tools/tools/bake/__init__.py` | НОВЫЙ | Маркер пакета. Ре-экспорт: `run_bake_pass`, `BakeStateGuard`, `BAKE_MAPS`, `composite_layers`, `bake_map_enum_items`. |
| `INU_tools/tools/bake/bake_core.py` | НОВЫЙ | **Слой 1.** `BakeStateGuard` (снапшот/восстановление `render.engine`, `cycles.samples/device/use_denoising`, `render.bake.*`, `world`, активные image-ноды, hide_render чужих ламп). `setup_target_image` (get-or-reuse + `img.scale`). `ensure/restore_bake_nodes` (`INU_bake_tex` + placeholder). `run_cycles_bake`. numpy I/O. |
| `INU_tools/tools/bake/bake_maps.py` | НОВЫЙ | **Слой 2.** `BakeMapDef` + `BAKE_MAPS`. Риги (`build_shadow_rig`, `build_diffuse_lit_rig`), `build_bevel_node_group` (Python, light-free), `prepare_map() -> teardown`. `bake_map_enum_items()` с кэшем. |
| `INU_tools/tools/bake/bake_composite.py` | НОВЫЙ | **Слой 3.** ЧИСТЫЙ numpy. `composite_layers`, `_BLEND` (NORMAL/MULTIPLY/ADD/OVERLAY/SCREEN), `apply_contrast_gamma` (сейчас identity), sRGB-encode (C1). |
| `INU_tools/ops/bake_ops.py` | НОВЫЙ | **Слой 4.** Операторы `GTATOOLS_OT_bake_run/_layer_add/_remove/_move`. Оркестрация, Cycles+UV guard, `report()+T()`, `REGISTER|UNDO`. |
| `INU_tools/scene_settings.py` | ПРАВКА | `INUBakeLayer` (PropertyGroup) рядом с `INUValidateIssue`; поля `gtatools_bake_*`; enum-proxy с кэшем. |
| `INU_tools/ui/panels.py` | ПРАВКА | `GTATOOLS_PT_bake_panel`, `GTATOOLS_PT_bake_advanced` (subpanel, дом будущих contrast/gamma/influence), `GTATOOLS_UL_bake_layers`. |
| `INU_tools/ui/registry.py` | ПРАВКА | `'GTATOOLS_PT_bake_panel': ('GTA_TOOLS','MODEL', 4)`. |
| `INU_tools/tools/profiles.py` | ПРАВКА (C7) | Добавить панель в `ALL_TOGGLEABLE_PANELS`/`KNOWN_PANELS`. |
| `INU_tools/tools/compat.py` | ПРАВКА | `HAS_NODE_INTERFACE` + `node_group_new_output()` helper. |
| `INU_tools/__init__.py` | ПРАВКА | Импорт ops; classes tuple (item-class рано, parent раньше subpanel); `gtatools_bake_layers` в SKIP; defensive sweep (НЕ трогать `Prelight_Lights` — C3). |
| `INU_tools/locale/eng.py` + `spa.py` | ПРАВКА | LANG-записи для новых строк. |

**Почему `INUBakeLayer` в `scene_settings.py`:** конвенция INU — CollectionProperty item-классы живут рядом с `INUValidateIssue` (чтобы `CollectionProperty(type=...)` резолвился без circular import).

---

## 3. Модель данных / настройки (масштабируемость без редизайна)

### 3.1. Реестр карт — `BAKE_MAPS` (НЕ bpy-тип)
```python
@dataclass(frozen=True)
class BakeMapDef:
    id: str                      # 'AO','DIFFUSE','DIFFUSE_LIT','SHADOW','BEVEL'
    label_key: str               # сырой русский ключ для T()
    bake_type: str               # 'AO'|'DIFFUSE'|'EMIT'
    needs_light: bool            # True -> риг + изоляция чужого света
    rig_kind: str                # 'NONE'|'SUN'|'PRELIGHT_8'
    node_group_builder: object   # callable|None (Bevel -> build_bevel_node_group)
    samples: int
    default_blend: str           # 'MULTIPLY'|'OVERLAY'|'NORMAL'
    default_opacity: float
    default_contrast: float      # 1.0 = identity (FUTURE)
    default_gamma: float         # 1.0 = identity (FUTURE)

BAKE_MAPS = OrderedDict([
  ('AO',          BakeMapDef('AO','Ambient Occlusion','AO', False,'NONE',      None,             16,'MULTIPLY',1.0,1.0,1.0)),
  ('DIFFUSE',     BakeMapDef('DIFFUSE','Diffuse (Albedo)','DIFFUSE',False,'NONE',None,            1,'NORMAL',  1.0,1.0,1.0)),
  ('DIFFUSE_LIT', BakeMapDef('DIFFUSE_LIT','Diffuse (Lit)','DIFFUSE',True,'PRELIGHT_8',None,      8,'NORMAL',  1.0,1.0,1.0)),
  ('SHADOW',      BakeMapDef('SHADOW','Shadow','DIFFUSE',  True, 'SUN',        None,             32,'MULTIPLY',1.0,1.0,1.0)),
  ('BEVEL',       BakeMapDef('BEVEL','Bevel','EMIT',       False,'NONE', build_bevel_node_group,  8,'OVERLAY', 1.0,1.0,1.0)),
])
```
**Diffuse раздваиваем явно** на `DIFFUSE` (albedo) и `DIFFUSE_LIT` (с внутренним светом) — без «variant field» в будущем.

### 3.2. Per-map слой стека — `INUBakeLayer` (PropertyGroup, `scene_settings.py`)
```python
class INUBakeLayer(bpy.types.PropertyGroup):
    map_id:     EnumProperty(items=_bake_map_enum_items_proxy)  # кэш в module-global (enum-GC gotcha)
    enabled:    BoolProperty(default=True)                       # «любой поднабор»
    blend_mode: EnumProperty(items=_BLEND_ITEMS, default='MULTIPLY')
    opacity:    FloatProperty(default=1.0, min=0.0, max=1.0)
    # ── FUTURE (объявлены сейчас, identity-дефолты, движок их УЖЕ читает) ──
    contrast:         FloatProperty(default=1.0, min=0.0, max=4.0)
    gamma:            FloatProperty(default=1.0, min=0.05, max=4.0)
    influence_target: StringProperty(default='')   # «влияние одной карты на другую» (masking)
    influence_amount: FloatProperty(default=1.0, min=0.0, max=1.0)
```

### 3.3. Scene-уровень — поля на `INUSceneSettings`
```python
gtatools_bake_composite_mode:  BoolProperty(default=False)            # ГЛАВНЫЙ опциональный тумблер
gtatools_bake_resolution:      EnumProperty(['512','1024','2048','4096'], default='1024')
gtatools_bake_samples:         IntProperty(default=16, min=1, max=512)
gtatools_bake_margin:          IntProperty(default=8, min=0, max=64)
gtatools_bake_result_name:     StringProperty(default='inu_bake')
gtatools_bake_show_advanced:   BoolProperty(default=False)
gtatools_bake_bevel_size:      FloatProperty(default=0.02, min=0.0)
gtatools_bake_bevel_samples:   IntProperty(default=8, min=2, max=64)
gtatools_bake_light_energy_scale: FloatProperty(default=1.0, min=0.0) # C5
gtatools_bake_layers:          CollectionProperty(type=INUBakeLayer)
gtatools_bake_layers_index:    IntProperty(default=0)
```

### 3.4. Как масштабируется без редизайна
- **contrast/gamma**: поля уже есть; `composite_layers` уже вызывает `apply_contrast_gamma()` (сегодня no-op). Включить = одна строка `layout.prop`.
- **influence (masking)**: поля `influence_target/amount` уже есть; в fold-цикле уже строка `fac = opacity * mask * influence_amount`. Резолвер маски дописывается без смены сигнатур.
- **новая карта**: одна запись `BAKE_MAPS` (+ опц. builder). Движок/композит/UI не трогаются.
- **новый blend**: одна запись в `_BLEND` + одна в `_BLEND_ITEMS`.

---

## 4. Движок запекания одной карты (`bake_core.run_bake_pass`)

**0. Предусловия (в операторе):**
- Cycles доступен и **включён** (через engine enum_items — C4); иначе `report({'ERROR'}, T('Включите Cycles'))`.
- **UV-guard**: активный непустой UV-слой; иначе понятная ошибка (авто-unwrap — будущая опция).
- Объект — mesh с полигонами.

**1. `with BakeStateGuard(context):`** (ОДИН на весь прогон — C9) — снапшот: `render.engine`, `cycles.device/samples/use_denoising`, `render.bake.{target,margin,use_pass_*,normal_*}`, `world`, активные ноды слотов, active object, mode. Затем: `engine='CYCLES'`, `bake.target='IMAGE_TEXTURES'`, `use_denoising=False`, `samples`, `margin`, форс OBJECT mode.

**2. Окружение** — `bake_maps.prepare_map` возвращает teardown (свет / node-группа / no-op). См. §5, §6.

**3. Целевая картинка + ноды:** `setup_target_image` (get-or-reuse по имени + `img.scale`, без delete → нет `.001`). Транзитные — `use_fake_user=False`, финал — `True`. На КАЖДОМ слоте `ensure_bake_node(mat)` создаёт/переиспользует `INU_bake_tex`, `node.image=target`, делает активной. Нет/пустой слот → временный `INU_bake_placeholder` материал.

**4. Проходы под карту:**
- `AO` → `type='AO'`.
- `DIFFUSE` (albedo) → `use_pass_color=True`, direct/indirect=False, `samples=1`.
- `DIFFUSE_LIT` → `use_pass_color=True, use_pass_direct=True`, `use_pass_indirect=False` (C2 — детерминизм без протечки чужой эмиссии).
- `SHADOW` → `use_pass_color=False, use_pass_direct=True, use_pass_indirect=False`.
- `BEVEL` → `type='EMIT'`.

**5. Вызов:** `bpy.ops.object.bake(type=..., use_clear=(first_slot), use_selected_to_active=False, margin=...)`. **`use_clear=True` только на ПЕРВОМ слоте**, далее `False` — аккумуляция вкладов всех слотов в одну картинку.

**6. Чтение:** ПОСЛЕ запекания — `read_image_to_numpy` → `(h,w,4) float32`. Никогда не читать ДО bake.

**7. Teardown карты:** снять риг/placeholder/node-группу, восстановить `hide_render`, `restore_bake_nodes`.

**8. `__exit__` (finally, ВСЕГДА):** восстановить ВСЕ снапшоты + world + engine, даже при exception/Cancel.

**Ошибки/undo:** `REGISTER|UNDO`; исключение → `__exit__` восстанавливает → `report({'ERROR'})`, `{'CANCELLED'}`.

---

## 5. Самодостаточный свет (КЛЮЧЕВОЕ)

**Цель:** пользователю НЕ надо ставить лампы, и результат НЕ зависит от его сцены/HDRI/чужих ламп.

### 5.1. Какие карты требуют свет
- **AO / BEVEL / DIFFUSE(albedo)** — `needs_light=False`, риг НЕ создаётся.
- **DIFFUSE_LIT** (`PRELIGHT_8`) и **SHADOW** (`SUN`) — единственные светозависимые.

### 5.2. Создание/удаление рига (внутри guard-скоупа)
1. Центр и max-dim объекта (через evaluated mesh, уважая модификаторы — как `prelight._eval_loop_normals`).
2. **DIFFUSE_LIT** → собственный 8-точечный риг в коллекции **`INU_Bake_Prelight`** (НЕ переиспользуем `Prelight_Lights` — C3). Энергия масштабируется `gtatools_bake_light_energy_scale` и `distance²` для масштаб-инвариантности (C5).
   **SHADOW** → **SUN-риг** (направленный, угол/мягкость в advanced) + слабый ambient-fill, коллекция **`INU_Bake_Lights`**.
3. **Изоляция чужого света (C2):** снапшот `hide_render` всех чужих LIGHT-объектов **И** (для light-проходов) прочих мешей с эмиссией → `hide_render=True` на время прохода + нейтральный constant-grey world. Восстановление в `__exit__`. Проверить, что коллекция рига не `exclude=True` в активном view layer (C10).
4. Teardown удаляет ТОЛЬКО собственные коллекции (`INU_Bake_*`), всегда в finally.

### 5.3. Детерминизм
Риг позиционируется относительно bbox-центра и масштабируется по max-dim → инвариантен к положению/масштабу. Нейтральный world + изоляция → воспроизводимо независимо от окружения.

---

## 6. Карты — AO / Diffuse / Shadow / Bevel

| Карта | `bake_type` | Свет | Детали |
|---|---|---|---|
| **AO** | `AO` | НЕТ | Нативная Cycles-окклюзия. `samples=16`. blend `MULTIPLY`. |
| **DIFFUSE** (albedo) | `DIFFUSE` | НЕТ | `use_pass_color`, `samples=1`. База стека, blend `NORMAL`. Несёт alpha. |
| **DIFFUSE_LIT** | `DIFFUSE` | ДА (PRELIGHT_8) | свет×альбедо. Калиброванная энергия (C5). |
| **SHADOW** | `DIFFUSE` | ДА (SUN) | `use_pass_color=False, use_pass_direct=True`. `samples=32`. blend `MULTIPLY`. |
| **BEVEL** | `EMIT` | НЕТ | Python node-группа. blend `OVERLAY`. |

### 6.1. Bevel node-группа в Python (light-free, без внешнего .blend)
1. `ng = bpy.data.node_groups.get('INU_Bevel_Bake') or ...new(...)` (get-or-reuse, без `.001`).
2. Сокеты — через `compat.node_group_new_output` (4.0+ `interface.new_socket` vs `outputs.new`; тип `NodeSocketShader` для surface — C6).
3. Ноды: `ShaderNodeBevel` (`Radius=bevel_size`, `.samples=bevel_samples`) → `Normal` ⊥ `ShaderNodeNewGeometry.Normal` через `VectorMath(DOT_PRODUCT)` → `MapRange` (clamp, настраиваемые From-Min/Max — C6) → `Emission` → Group Output.
4. Обёртка-материал `INU_Bevel_Mat`; `type='EMIT'` → light-free.

### 6.2. Задел под «другие»
`CAVITY/THICKNESS/CURVATURE` — каждая = одна запись `BAKE_MAPS` (+ опц. builder). Доказательство в роадмапе M7.

---

## 7. Композит «N карт → одна текстура»

`bake_composite.composite_layers(layer_pixels, layer_structs, w, h) -> ndarray` — чистый numpy. **Вход — обычные dataclass/tuple, не PropertyGroup** (C8).

**Единое разрешение:** все слои в composite-режиме — в `gtatools_bake_resolution`; `_resample_to()` для нештатных размеров.

**Алгоритм (снизу вверх):**
```python
acc_rgb = base[..., :3]          # нижний enabled-слой
base_alpha = base[..., 3]        # alpha базового diffuse — НЕСЁМ до конца (cutout/листва SA)
for layer in enabled_layers[1:]:
    top = apply_contrast_gamma(layer_pixels[layer.map_id][..., :3], layer.contrast, layer.gamma)  # FUTURE: identity
    blended = _BLEND[layer.blend_mode](acc_rgb, top)
    fac = layer.opacity * mask_lookup.get(layer.influence_target, 1.0) * layer.influence_amount    # FUTURE
    acc_rgb = acc_rgb * (1.0 - fac) + blended * fac
acc_rgb = linear_to_srgb(np.clip(acc_rgb, 0, 1))   # C1 — кодируем в sRGB перед записью
out = np.dstack([acc_rgb, base_alpha])             # alpha — из базового diffuse
return out
```
```python
_BLEND = {
  'NORMAL':   lambda a, b: b,
  'MULTIPLY': lambda a, b: a * b,
  'ADD':      lambda a, b: np.clip(a + b, 0, 1),
  'SCREEN':   lambda a, b: 1 - (1 - a) * (1 - b),
  'OVERLAY':  lambda a, b: np.where(a < 0.5, 2*a*b, 1 - 2*(1-a)*(1-b)),
}
```

**GTA SA сценарий:** база `DIFFUSE`(albedo) → `MULTIPLY` `AO` → `MULTIPLY` `SHADOW` → `OVERLAY` `BEVEL` → одна diffuse-текстура. Alpha cutout сохранена, цвет в sRGB.

**Опциональность:** `composite_layers` вызывается **только** при `gtatools_bake_composite_mode == True`. Иначе — per-map `<output>_<map_id>`, `bake_composite` не импортируется.

---

## 8. UI

**Размещение:** MODEL-зона, `'GTATOOLS_PT_bake_panel': ('GTA_TOOLS','MODEL', 4)` → bl_order 14, коллизий нет.

**`GTATOOLS_PT_bake_panel`** (`@apply_order`, parent `GTATOOLS_PT_main_panel`, DEFAULT_CLOSED): разрешение/samples/margin/имя; **главный тумблер** `gtatools_bake_composite_mode` (toggle); `template_list` стека слоёв + кнопки add/remove/move; detail выбранного слоя (`blend_mode`/`opacity` с `layout.enabled = composite_mode`); большая кнопка `gtatools.bake_run`.

**`GTATOOLS_PT_bake_advanced`** (subpanel, DEFAULT_CLOSED): дом будущих contrast/gamma/influence + сегодня bevel size/samples, shadow angle, light_energy_scale, auto-unwrap.

**`GTATOOLS_UL_bake_layers`** (шаблон `GTATOOLS_UL_lint_issues`): чекбокс `enabled` (HIDE_OFF/ON), `T(BAKE_MAPS[item.map_id].label_key)`, blend+opacity inline.

**Операторы:** `bake_run`, `bake_layer_add` (per-map дефолты из `BAKE_MAPS`), `bake_layer_remove`, `bake_layer_move`.

---

## 9. Регистрация / локализация

1. `scene_settings.py`: `INUBakeLayer` рядом с `INUValidateIssue`; `_bake_map_enum_items_proxy` с кэшем в module-global (enum-GC); поля `gtatools_bake_*`.
2. `tools/compat.py`: `HAS_NODE_INTERFACE = BL >= (4,0,0)` + `node_group_new_output()`.
3. `tools/bake/`: 4 import-only модуля (не в `classes`).
4. `ops/bake_ops.py`: операторы; `bl_label`/`bl_description` — сырые русские строки; `report()` через `T()`.
5–6. `__init__.py`: импорт ops; classes tuple — `INUBakeLayer` ДО `INUSceneSettings`; parent-панель ДО subpanel.
7. `__init__.py`: `gtatools_bake_layers` в SKIP set (безвредно; формулировку «иначе упадёт» — убрать, C-info).
8. `__init__.py`: defensive sweep удаляет ТОЛЬКО `INU_Bevel_*`/`INU_bake_*`/`INU_Bake_Lights`/`INU_Bake_Prelight` — **НЕ `Prelight_Lights`** (C3).
9. `ui/registry.py`: одна строка; `@apply_order` в `panels.py`. + `tools/profiles.py` whitelist (C7).
10. `locale/eng.py`+`spa.py`: LANG-ключи.
11. **БЕЗ** `from __future__ import annotations` в модулях с PropertyGroup. **БЕЗ** изменений манифеста → нулевое влияние на ревью.
12. `unregister()`: через `reversed(classes)` + sweep из п.8.

---

## 10. Дорожная карта по этапам

Всё — в минорные версии (текущая 2.0.3). Влияние на pending review — **нулевое** на каждом этапе.

| Этап | Что | Усилие | Версия |
|---|---|---|---|
| **M1** | `bake_core`: `BakeStateGuard` (+ изоляция), image/node setup, `run_cycles_bake`, numpy I/O. + `compat` helper. Smoke-тест. | M (2–3 дн) | 2.1.0-dev |
| **M2** | `bake_maps`: AO + Bevel (Python node-группа + MapRange). Light-free путь end-to-end. | M (2 дн) | 2.1.0-dev |
| **M3** | Светозависимые: SUN-Shadow, PRELIGHT_8 Diffuse-Lit (калибровка C5), изоляция чужого света (C2), собственные коллекции (C3), teardown. | M (2–3 дн) | 2.1.0-dev |
| **M4** | `bake_composite`: `composite_layers` + `_BLEND` + opacity + единое разрешение + alpha базового + **sRGB-encode (C1)**. Pure-numpy юнит-тесты (вкл. C1 round-trip). | M (2–3 дн) | 2.1.0-dev |
| **M5** | `ops/bake_ops` + модель данных + wiring + guards. Composite-ON → одна картинка; OFF → per-map. | M (2 дн) | 2.1.0 |
| **M6** | UI + локализация + profiles whitelist (C7). End-to-end UX. | S (1–2 дн) | 2.1.0 |
| **M7** | Полировка + GTA-SA валидация на реальных DFF + одна «другая» карта (Cavity) как доказательство расширяемости. | S (1 дн) | 2.1.1 |
| **M8 (FUTURE)** | Раскрытие contrast/gamma/influence (UI-only) + интеграция в SA-материал/TXD-экспорт. | S (1–2 дн) | 2.2.0 |

---

## 11. Решения и открытые вопросы

### Зафиксировано пользователем (2026-06-03)
- ✅ **Diffuse — ОБА варианта:** `DIFFUSE` (albedo, база композита) + `DIFFUSE_LIT` (альбедо×внутренний свет). Обе записи остаются в `BAKE_MAPS`.
- ✅ **Нет UV → ошибка + подсказка** через `report({'ERROR'}, T(...))`, отмена. Данные пользователя НЕ трогаем (никакого авто-unwrap). Поле `gtatools_bake_auto_unwrap` НЕ добавляем в MVP.
- ✅ **Результат — только картинка** (запакованное Blender-изображение). Автоподключение в Base Color и TXD-экспорт **из MVP исключены**; seam под них (M8) сохраняется, но не реализуется сейчас.

### Остаётся открытым (не блокирует старт, решим по ходу)
1. **Калибровка экспозиции внутреннего рига (C5):** целевой уровень яркости для SA (серый ~0.5?). Подбирается эмпирически на M3.
2. **Shadow-каст:** фиксированное направление SUN (~45° NW) в MVP, контроль угла — в advanced позже.
3. **Per-object vs scene-global** настройки стека (сейчас глобально, как prelight) — заложен только seam.
4. **Разрешение** по умолчанию (1024) / максимум (4096) — память при float32 × много слоёв.
5. **Цветовое пространство (C1):** sRGB-кодирование финала — закрыто в плане как обязательное; подтвердить на реальной SA-текстуре (M4/M7).
