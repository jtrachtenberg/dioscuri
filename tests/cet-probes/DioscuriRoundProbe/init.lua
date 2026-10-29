-- TEMPORARY diagnostic (Dioscuri visible rounds, 2026-10-29): where the game
-- puts the bolt's and each round's moving bone, read through the test build's
-- probe slots (mesh-work\finish_moving_parts.py --probe-slots).
-- The bolt is the control: it is known to move in game (cocking_mechanism,
-- y 0.108 closed -> 0.008 open in the gun frame). If the rounds' mag_std bones
-- stay put while the bolt moves, their clips are not playing.
-- Positions are in the weapon entity's frame (+Y muzzle, +Z up), metres; a
-- line is written whenever any bone moved more than 0.5 mm, plus a heartbeat
-- every 2 s. Lines go to round_probe.txt in this folder, appended and closed
-- each time. Delete this folder when done.

local PROBES = { "DioscuriProbeBolt", "DioscuriProbeRoundA", "DioscuriProbeRoundB" }
local MESHES = { "dioscuri_round_a_mesh", "dioscuri_round_b_mesh" }
local SAMPLE = 0.05
local MAX_LINES = 20000

local lines = 0
local errors = 0
local clock = 0
local nextSample = 0
local lastBeat = -100
local last = {}
local lastWeapon = nil

local function rec(s)
    if lines >= MAX_LINES then return end
    lines = lines + 1
    local h = io.open("round_probe.txt", "a")
    if h then
        h:write(string.format("%s %8.2f %s\n", os.date("%H:%M:%S"), clock, s))
        h:close()
    end
end

-- v rotated by the inverse of unit quaternion q
local function unrotate(q, x, y, z)
    local qx, qy, qz, qw = -q.i, -q.j, -q.k, q.r
    local tx = 2 * (qy * z - qz * y)
    local ty = 2 * (qz * x - qx * z)
    local tz = 2 * (qx * y - qy * x)
    return x + qw * tx + (qy * tz - qz * ty),
           y + qw * ty + (qz * tx - qx * tz),
           z + qw * tz + (qx * ty - qy * tx)
end

local function qmulConj(a, b)  -- conj(a) * b
    local ax, ay, az, aw = -a.i, -a.j, -a.k, a.r
    return {
        i = aw * b.i + ax * b.r + ay * b.k - az * b.j,
        j = aw * b.j - ax * b.k + ay * b.r + az * b.i,
        k = aw * b.k + ax * b.j - ay * b.i + az * b.r,
        r = aw * b.r - ax * b.i - ay * b.j - az * b.k,
    }
end

local function sample()
    local player = Game.GetPlayer()
    if not player then return end
    local w = Game.GetTransactionSystem():GetItemInSlot(player, TweakDBID.new("AttachmentSlots.WeaponRight"))
    if not w then return end
    local wid = tostring(w:GetEntityID().hash)
    local first = (wid ~= lastWeapon)
    lastWeapon = wid
    if first then
        local found = {}
        for _, n in ipairs(PROBES) do
            found[#found + 1] = n .. "=" .. tostring(w:FindComponentByName(CName.new(n)) ~= nil)
        end
        for _, n in ipairs(MESHES) do
            local c = w:FindComponentByName(CName.new(n))
            local en = "?"
            if c then pcall(function() en = tostring(c:IsEnabled()) end) end
            found[#found + 1] = n .. "=" .. tostring(c ~= nil) .. "/enabled " .. en
        end
        rec("weapon " .. wid .. " " .. table.concat(found, " "))
        last = {}
    end
    local wp = w:GetWorldPosition()
    local wq = w:GetWorldOrientation()
    local parts, moved = {}, false
    for _, n in ipairs(PROBES) do
        local c = w:FindComponentByName(CName.new(n))
        local txt = n .. " -"
        if c then
            local ok, wt = c:GetSlotTransform(CName.new("probe"))
            if ok then
                local p = WorldPosition.ToVector4(WorldTransform.GetWorldPosition(wt))
                local q = WorldTransform.GetOrientation(wt)
                local x, y, z = unrotate(wq, p.x - wp.x, p.y - wp.y, p.z - wp.z)
                local lq = qmulConj(wq, q)
                local l = last[n]
                if not l or math.abs(l[1] - x) + math.abs(l[2] - y) + math.abs(l[3] - z) > 0.0005 then
                    moved = true
                end
                last[n] = { x, y, z }
                txt = string.format("%s %.4f %.4f %.4f q %.4f %.4f %.4f %.4f", n, x, y, z, lq.i, lq.j, lq.k, lq.r)
            else
                txt = n .. " noslot"
            end
        end
        parts[#parts + 1] = txt
    end
    if moved or clock - lastBeat >= 2 then
        lastBeat = clock
        rec((moved and "" or "beat ") .. table.concat(parts, " | "))
    end
end

registerForEvent("onInit", function()
    rec("init")
end)

registerForEvent("onUpdate", function(dt)
    clock = clock + dt
    if clock < nextSample then return end
    nextSample = clock + SAMPLE
    local ok, e = pcall(sample)
    if not ok then
        errors = errors + 1
        if errors <= 20 then rec("ERR " .. tostring(e)) end
    end
end)
