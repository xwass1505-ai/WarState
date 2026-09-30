-- ConstructionService: PLANNED -> UNDER_CONSTRUCTION -> COMPLETED over time.
-- Visuals: planned = faint ghost; under construction = parts become solid from the ground up
-- plus a small progress bar that is REMOVED on completion (no permanent floating labels).
-- Construction advances only while the owner is in the session (progress is saved).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))

local ConstructionService = {}
ConstructionService.Name = "ConstructionService"

local services
local tracked = {} -- [Player] = { [Id] = { record, model, parts } }

local defsById = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	defsById[def.Id] = def
end

local GHOST = GameConfig.Construction.GhostTransparency
local ACCENT = Color3.fromRGB(84, 156, 230)

local function collectParts(model)
	local parts = {}
	local pivotY = model:GetPivot().Position.Y
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") and d.Name ~= "Root" then
			local base = d:GetAttribute("BaseTransparency") or 0
			local bottom = d.Position.Y - d.Size.Y / 2 - pivotY
			table.insert(parts, { part = d, base = base, bottom = bottom })
		end
	end
	return parts
end

local function ensureProgressBar(entry)
	local model = entry.model
	local existing = model:FindFirstChild("ConstructionProgress")
	if existing then
		return existing
	end
	local height = model:GetAttribute("VisualHeight") or 6
	local gui = Instance.new("BillboardGui")
	gui.Name = "ConstructionProgress"
	gui.Size = UDim2.fromOffset(64, 8)
	gui.StudsOffsetWorldSpace = Vector3.new(0, height + 1.5, 0)
	gui.MaxDistance = GameConfig.Construction.ProgressBarMaxDistance
	gui.AlwaysOnTop = false
	gui.LightInfluence = 0
	gui.Adornee = model.PrimaryPart

	local back = Instance.new("Frame")
	back.Name = "Back"
	back.Size = UDim2.fromScale(1, 1)
	back.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
	back.BorderSizePixel = 0
	back.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(1, 0)
	corner.Parent = back

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.fromScale(0, 1)
	fill.BackgroundColor3 = ACCENT
	fill.BorderSizePixel = 0
	fill.Parent = back
	local fillCorner = Instance.new("UICorner")
	fillCorner.CornerRadius = UDim.new(1, 0)
	fillCorner.Parent = fill

	gui.Parent = model
	return gui
end

local function applyVisual(entry)
	local record = entry.record
	local model = entry.model
	local def = defsById[record.Type]
	model:SetAttribute("State", record.State)
	if record.State == Constants.BuildState.Completed then
		for _, info in ipairs(entry.parts) do
			info.part.Transparency = info.base
		end
		local bar = model:FindFirstChild("ConstructionProgress")
		if bar then
			bar:Destroy()
		end
		model:SetAttribute("Progress", 1)
		return
	end

	local fraction = 0
	if record.State == Constants.BuildState.UnderConstruction then
		fraction = math.clamp(record.Progress / def.BuildTimeSeconds, 0, 1)
	end
	model:SetAttribute("Progress", fraction)
	local height = model:GetAttribute("VisualHeight") or 6
	local revealHeight = fraction * height
	for _, info in ipairs(entry.parts) do
		if record.State == Constants.BuildState.UnderConstruction and info.bottom <= revealHeight then
			info.part.Transparency = info.base
		else
			info.part.Transparency = math.max(info.base, GHOST)
		end
	end
	local bar = ensureProgressBar(entry)
	local fill = bar:FindFirstChild("Back") and bar.Back:FindFirstChild("Fill")
	if fill then
		fill.Size = UDim2.fromScale(math.max(fraction, 0.04), 1)
	end
end

function ConstructionService.track(player: Player, record, model)
	tracked[player] = tracked[player] or {}
	local entry = { record = record, model = model, parts = collectParts(model) }
	tracked[player][record.Id] = entry
	applyVisual(entry)
end

function ConstructionService.clearPlayer(player: Player)
	tracked[player] = nil
end

local function step(dt: number)
	for player, entries in pairs(tracked) do
		local changedCapacity = false
		local anyActive = false
		for id, entry in pairs(entries) do
			local record = entry.record
			local def = defsById[record.Type]
			if record.State == Constants.BuildState.Planned then
				anyActive = true
				record.PlannedElapsed += dt
				if record.PlannedElapsed >= GameConfig.Construction.PlannedSeconds then
					record.State = Constants.BuildState.UnderConstruction
				end
				applyVisual(entry)
			elseif record.State == Constants.BuildState.UnderConstruction then
				anyActive = true
				record.Progress = math.min(record.Progress + dt, def.BuildTimeSeconds)
				if record.Progress >= def.BuildTimeSeconds then
					record.State = Constants.BuildState.Completed
					changedCapacity = true
					services.CountryService.notify(player, def.DisplayName .. " completed", "success")
				end
				applyVisual(entry)
			end
			if record.State == Constants.BuildState.Completed then
				entries[id] = nil
			end
		end
		if anyActive then
			services.DataService.markDirty(player)
		end
		if changedCapacity then
			local country = services.DataService.getCountry(player)
			if country then
				services.PopulationService.recalculate(country)
			end
		end
		if anyActive or changedCapacity then
			services.CountryService.push(player)
		end
	end
end

function ConstructionService.init(allServices)
	services = allServices
end

function ConstructionService.start()
	task.spawn(function()
		local interval = GameConfig.Construction.TickSeconds
		local last = os.clock()
		while true do
			task.wait(interval)
			local now = os.clock()
			local dt = now - last
			last = now
			local ok, err = pcall(step, dt)
			if not ok then
				warn("[ConstructionService] " .. tostring(err))
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		tracked[player] = nil
	end)
end

return ConstructionService
