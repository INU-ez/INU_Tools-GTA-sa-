-- INU Hair Attach — клиент.
--
-- Как это работает:
--   1. engineRequestModel("object") выдаёт свободный model ID (ванильные
--      модели НЕ замещаются, ничего в игре не ломается);
--   2. engineLoadTXD/engineImportTXD + engineLoadDFF/engineReplaceModel
--      загружают в него ассет, экспортированный из INU Tools;
--   3. createObject создаёт объект, коллизии выключены;
--   4. attachElementToBone цепляет объект к кости — но ТОЛЬКО НА ОДИН КАДР,
--      поэтому вызов живёт в onClientPedsProcessed: событие срабатывает уже
--      после того, как игра посчитала скелеты педов, — привязка без дрожания.

local models = {}          -- name -> { id = , dff = , txd = }
local worn   = {}          -- ped  -> { obj = , name = , def = }

local PARENT_OBJECT = 1337 -- донор для engineRequestModel (обычный объект)


-- ── Загрузка ассета в свободный model ID ─────────────────────────
local function loadModel(name)
    if models[name] then return models[name] end

    local def = HAIR[name]
    if not def then return nil end

    local id = engineRequestModel("object", PARENT_OBJECT)
    if not id then
        outputDebugString("[INU hair] нет свободного model ID для " .. name, 1)
        return nil
    end

    local txd = engineLoadTXD(def.txd)
    if txd then
        engineImportTXD(txd, id)
    else
        outputDebugString("[INU hair] не загрузился TXD: " .. tostring(def.txd), 2)
    end

    local dff = engineLoadDFF(def.dff)
    if not dff or not engineReplaceModel(dff, id) then
        outputDebugString("[INU hair] не загрузился DFF: " .. tostring(def.dff), 1)
        engineFreeModel(id)
        return nil
    end

    engineSetModelLODDistance(id, def.lod or 170)
    models[name] = { id = id, dff = dff, txd = txd }
    return models[name]
end


-- ── Надеть / снять ───────────────────────────────────────────────
local function detach(ped)
    local w = worn[ped]
    if not w then return end
    if isElement(w.obj) then destroyElement(w.obj) end
    worn[ped] = nil
end

local function attach(ped, name)
    detach(ped)

    local m = loadModel(name)
    if not m then return end
    local def = HAIR[name]

    local obj = createObject(m.id, 0, 0, 0)
    if not obj then return end

    setElementCollisionsEnabled(obj, false)
    setObjectBreakable(obj, false)
    setElementDoubleSided(obj, true)   -- волосы почти всегда односторонние плоскости
    if def.scale and def.scale ~= 1.0 then
        setObjectScale(obj, def.scale)
    end

    worn[ped] = { obj = obj, name = name, def = def }
end

-- Синхронизация с element data педа.
local function refresh(ped)
    if not isElement(ped) then return end
    local name = getElementData(ped, HAIR_DATA_KEY)
    if type(name) ~= "string" or not HAIR[name] then
        detach(ped)
        return
    end
    if worn[ped] and worn[ped].name == name then return end
    attach(ped, name)
end


-- ── Покадровая привязка ──────────────────────────────────────────
addEventHandler("onClientPedsProcessed", root, function()
    for ped, w in pairs(worn) do
        if not isElement(ped) or not isElement(w.obj) then
            worn[ped] = nil
        else
            -- Ped вне стрима / мёртв → attachElementToBone не вызываем,
            -- иначе объект зависнет там, где был в последний кадр.
            local show = isElementStreamedIn(ped) and not isPedDead(ped)
            if show then
                if getElementAlpha(w.obj) ~= 255 then setElementAlpha(w.obj, 255) end
                setElementDimension(w.obj, getElementDimension(ped))
                setElementInterior(w.obj, getElementInterior(ped))

                local d = w.def
                attachElementToBone(w.obj, ped, d.bone,
                    d.pos[1], d.pos[2], d.pos[3],
                    math.rad(d.rot[1]), math.rad(d.rot[2]), math.rad(d.rot[3]))
            elseif getElementAlpha(w.obj) ~= 0 then
                setElementAlpha(w.obj, 0)
            end
        end
    end
end)


-- ── Реакция на element data / стрим / удаление ───────────────────
addEventHandler("onClientElementDataChange", root, function(key)
    if key ~= HAIR_DATA_KEY then return end
    local t = getElementType(source)
    if t == "ped" or t == "player" then refresh(source) end
end)

addEventHandler("onClientElementStreamIn", root, function()
    local t = getElementType(source)
    if t == "ped" or t == "player" then refresh(source) end
end)

addEventHandler("onClientElementDestroy", root, function()
    if worn[source] then detach(source) end
end)

addEventHandler("onClientPlayerQuit", root, function()
    detach(source)
end)

addEventHandler("onClientResourceStart", resourceRoot, function()
    for _, ped in ipairs(getElementsByType("ped"))    do refresh(ped) end
    for _, ply in ipairs(getElementsByType("player")) do refresh(ply) end
end)

addEventHandler("onClientResourceStop", resourceRoot, function()
    for ped in pairs(worn) do detach(ped) end
    -- engineFreeModel обязателен: выданные ID сами не освобождаются.
    for _, m in pairs(models) do engineFreeModel(m.id) end
    models = {}
end)


-- =================================================================
--  Режим подгонки: /hairadj
--  Правит pos/rot/scale надетого НА СЕБЯ ассета вживую, /hairsave
--  печатает готовую строку для hair_defs.lua.
-- =================================================================
local adjust     = false
local POS_STEP   = 0.35   -- метров в секунду удержания
local ROT_STEP   = 45.0   -- градусов в секунду
local SCALE_STEP = 0.35   -- долей в секунду

-- { клавиша, индекс компоненты, знак }
local POS_KEYS = {
    { "num_4", 1, -1 }, { "num_6", 1,  1 },   -- X
    { "num_8", 2,  1 }, { "num_2", 2, -1 },   -- Y
    { "num_9", 3,  1 }, { "num_3", 3, -1 },   -- Z
}
local ROT_KEYS = {
    { "arrow_l", 1, -1 }, { "arrow_r", 1,  1 },
    { "arrow_u", 2,  1 }, { "arrow_d", 2, -1 },
    { "pgup",    3,  1 }, { "pgdn",    3, -1 },
}

local function fmt3(t)
    return string.format("%.3f, %.3f, %.3f", t[1], t[2], t[3])
end

local function hudDraw()
    local w = worn[localPlayer]
    if not w then
        dxDrawText("INU hair: ничего не надето (/hair <ключ>)",
                   20, 200, 0, 0, tocolor(255, 120, 120), 1.2, "default-bold")
        return
    end
    local d = w.def
    local lines = {
        "INU Hair Adjust — " .. (d.label or w.name),
        "pos   { " .. fmt3(d.pos) .. " }   num 4/6, 8/2, 9/3",
        "rot   { " .. fmt3(d.rot) .. " }   стрелки + PgUp/PgDn",
        "scale " .. string.format("%.3f", d.scale or 1.0) .. "   num +/-",
        "/hairsave — вывести строку для hair_defs.lua",
    }
    for i, line in ipairs(lines) do
        dxDrawText(line, 21, 199 + (i - 1) * 18, 0, 0,
                   tocolor(0, 0, 0, 200), 1.1, "default-bold")
        dxDrawText(line, 20, 198 + (i - 1) * 18, 0, 0,
                   i == 1 and tocolor(255, 220, 120) or tocolor(230, 230, 230),
                   1.1, "default-bold")
    end
end

local lastTick = getTickCount()
local function hudTick()
    local now = getTickCount()
    local dt  = math.min((now - lastTick) / 1000, 0.1)
    lastTick  = now

    local w = worn[localPlayer]
    if w then
        local d = w.def
        for _, k in ipairs(POS_KEYS) do
            if getKeyState(k[1]) then
                d.pos[k[2]] = d.pos[k[2]] + k[3] * POS_STEP * dt
            end
        end
        for _, k in ipairs(ROT_KEYS) do
            if getKeyState(k[1]) then
                d.rot[k[2]] = d.rot[k[2]] + k[3] * ROT_STEP * dt
            end
        end
        local ds = 0
        if getKeyState("num_add") then ds =  SCALE_STEP * dt end
        if getKeyState("num_sub") then ds = -SCALE_STEP * dt end
        if ds ~= 0 then
            d.scale = math.max(0.05, (d.scale or 1.0) + ds)
            if isElement(w.obj) then setObjectScale(w.obj, d.scale) end
        end
    end

    hudDraw()
end

addCommandHandler("hairadj", function()
    adjust = not adjust
    if adjust then
        lastTick = getTickCount()
        addEventHandler("onClientRender", root, hudTick)
        outputChatBox("Режим подгонки ВКЛ. /hairsave — вывести цифры.", 255, 220, 120)
    else
        removeEventHandler("onClientRender", root, hudTick)
        outputChatBox("Режим подгонки ВЫКЛ.", 200, 200, 200)
    end
end)

addCommandHandler("hairsave", function()
    local w = worn[localPlayer]
    if not w then
        outputChatBox("Ничего не надето.", 255, 120, 120)
        return
    end
    local d = w.def
    local block = string.format(
        "pos = { %.3f, %.3f, %.3f }, rot = { %.3f, %.3f, %.3f }, scale = %.3f,",
        d.pos[1], d.pos[2], d.pos[3], d.rot[1], d.rot[2], d.rot[3], d.scale or 1.0)
    outputChatBox("[" .. w.name .. "] " .. block, 150, 255, 180)
    outputDebugString("[INU hair] " .. w.name .. ": " .. block)
end)
