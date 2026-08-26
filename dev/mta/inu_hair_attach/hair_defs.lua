-- INU Hair Attach — общий каталог ассетов (shared: читают и сервер, и клиент).
--
-- bone   — ID кости MTA. Голова = 8 (BONE_HEAD). Другие полезные:
--          5 NECK, 7 HEAD1, 4 UPPERTORSO, 3 SPINE1,
--          25 R.HAND, 35 L.HAND, 22 R.SHOULDER, 32 L.SHOULDER.
-- pos    — смещение от кости в МЕТРАХ {x, y, z} (объект цепляется своим origin).
-- rot    — доворот в ГРАДУСАХ {x, y, z}.
-- scale  — множитель размера (1.0 = как экспортировано).
-- lod    — дистанция прорисовки, м.
--
-- Числа в pos/rot подбираются в игре: /hairadj (см. README).

HAIR = {
    ["afro_long"] = {
        label = "Афро (длинное)",
        dff   = "models/afro_long.dff",
        txd   = "models/afro_long.txd",
        bone  = 8,
        pos   = { 0.0, 0.0, 0.0 },
        rot   = { 0.0, 0.0, 0.0 },
        scale = 1.0,
        lod   = 170,
    },
}

-- Ключ element data, по которому клиент узнаёт, что надето на педе.
HAIR_DATA_KEY = "inu:hair"
