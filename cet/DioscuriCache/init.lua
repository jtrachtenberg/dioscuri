-- DioscuriCache (cleanup only): removes legacy dynamic cases from older
-- experiments. The real case comes from the world sector (see HANDOFF.md).
local timer = 0
registerForEvent("onUpdate", function(dt)
    timer = timer + dt
    if timer < 3.0 then return end
    timer = 0
    if not Game.GetPlayer() then return end
    local des = Game.GetDynamicEntitySystem()
    for _, tag in ipairs({ "DioscuriCache", "DioscuriCacheProp" }) do
        for _, id in ipairs(des:GetTaggedIDs(tag) or {}) do
            des:DeleteEntity(id)
        end
    end
end)
return {}
