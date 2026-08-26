-- INU Hair Attach — сервер.
-- Сервер только помечает педа element data; всю отрисовку делает клиент.

--- Надеть причёску на педа/игрока.
-- @param thePed  ped/player
-- @param name    ключ из HAIR или nil/false, чтобы снять
function wearHair(thePed, name)
    if not isElement(thePed) then return false end
    local t = getElementType(thePed)
    if t ~= "ped" and t ~= "player" then return false end

    if name == nil or name == false or name == "" then
        removeElementData(thePed, HAIR_DATA_KEY)
        return true
    end
    if not HAIR[name] then return false end

    setElementData(thePed, HAIR_DATA_KEY, name)
    return true
end

--- Снять всё с педа.
function removeHair(thePed)
    return wearHair(thePed, nil)
end

--- Список доступных ключей (для меню/UI другого ресурса).
function getHairList()
    local out = {}
    for key, def in pairs(HAIR) do
        out[key] = def.label or key
    end
    return out
end


-- ── Команда для тестов: /hair <ключ>, /hair — снять ──────────────
addCommandHandler("hair", function(player, _, name)
    if not name then
        removeHair(player)
        outputChatBox("Причёска снята.", player, 255, 200, 100)
        return
    end
    if not HAIR[name] then
        outputChatBox("Нет такой причёски: " .. name, player, 255, 100, 100)
        local list = {}
        for key in pairs(HAIR) do list[#list + 1] = key end
        outputChatBox("Доступно: " .. table.concat(list, ", "), player, 200, 200, 200)
        return
    end
    wearHair(player, name)
    outputChatBox("Надето: " .. (HAIR[name].label or name), player, 100, 255, 150)
end)
