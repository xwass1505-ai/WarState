-- BuildingService: server-authoritative building placement.
-- Client sends {Type, Variant, X, Z, Rotation}; the server snaps, validates (territory, overlap,
-- road access within PlacementConfig.MaxRoadDistance) and creates a PLANNED building that the
-- ConstructionService then builds over time.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local Modules = Shared:WaitForChild("Modules")
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local BuildingModels = require(Modules:WaitForChild("BuildingModels"))

local BuildingService = {}
BuildingService.Name = "BuildingService"

local services
local remotes
local runtime = {} -- [Player] = { models = {Id -> Model}, rects = {Id -> Rect} }
local lastRequest = {}

local defsById = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	defsById[def.Id] = def
end

function BuildingService.getDef(typeId: string)
	return defsById[typeId]
end

local function getRuntime(player)
	local r = runtime[player]
	if not r then
		r = { models = {}, rects = {} }
		runtime[player] = r
	end
	return r
end

local function worldRect(record, bounds)
	local def = defsById[record.Type]
	local width, depth = GridMath.rotatedSize(def.Footprint[1], def.Footprint[2], record.Rotation)
	return GridMath.rect(bounds.minX + record.X, bounds.minZ + record.Z, width, depth)
end

local function spawnModel(player, record)
	local folder = services.WorldService.getPlotFolder(player, "Buildings")
	local bounds = services.WorldService.getBounds(player)
	local def = defsById[record.Type]
	if not folder or not bounds or not def then
		return nil
	end
	local r = getRuntime(player)
	local old = r.models[record.Id]
	if old then
		old:Destroy()
	end
	local model = BuildingModels.build(def, record.Variant)
	model.Name = record.Id
	local wx, wz = bounds.minX + record.X, bounds.minZ + record.Z
	model:PivotTo(CFrame.new(wx, bounds.surfaceY, wz) * CFrame.Angles(0, GridMath.yawForRotation(record.Rotation), 0))
	local rect = worldRect(record, bounds)
	model:SetAttribute(Constants.Attributes.Kind, "Building")
	model:SetAttribute(Constants.Attributes.TypeId, record.Type)
	model:SetAttribute("Variant", record.Variant)
	model:SetAttribute("RectMinX", rect.minX)
	model:SetAttribute("RectMaxX", rect.maxX)
	model:SetAttribute("RectMinZ", rect.minZ)
	model:SetAttribute("RectMaxZ", rect.maxZ)
	model:SetAttribute("State", record.State)
	model.Parent = folder
	r.models[record.Id] = model
	r.rects[record.Id] = rect
	return model
end

function BuildingService.getModel(player: Player, id: string)
	local r = runtime[player]
	return r and r.models[id] or nil
end

function BuildingService.getBuildingRects(player: Player)
	local result = {}
	local r = runtime[player]
	if r then
		for _, rect in pairs(r.rects) do
			table.insert(result, rect)
		end
	end
	return result
end

function BuildingService.loadCountry(player: Player, country)
	BuildingService.clearPlayer(player)
	for _, record in pairs(country.Buildings) do
		if defsById[record.Type] and BuildingModels.hasVariant(record.Variant) then
			local model = spawnModel(player, record)
			if model then
				services.ConstructionService.track(player, record, model)
			end
		else
			warn("[BuildingService] Skipping unknown saved building " .. tostring(record.Type))
		end
	end
end

function BuildingService.clearPlayer(player: Player)
	local r = runtime[player]
	if r then
		for _, model in pairs(r.models) do
			model:Destroy()
		end
	end
	runtime[player] = nil
end

local function handlePlace(player, request)
	local now = os.clock()
	if lastRequest[player] and now - lastRequest[player] < PlacementConfig.RequestCooldown then
		return { ok = false, error = "Too fast" }
	end
	lastRequest[player] = now

	local country = services.DataService.getCountry(player)
	local bounds = services.WorldService.getBounds(player)
	if not country or not bounds then
		return { ok = false, error = "No active state" }
	end
	if type(request) ~= "table" or type(request.X) ~= "number" or type(request.Z) ~= "number" then
		return { ok = false, error = "Invalid request" }
	end
	if request.X ~= request.X or request.Z ~= request.Z then
		return { ok = false, error = "Invalid request" }
	end
	local def = type(request.Type) == "string" and defsById[request.Type] or nil
	if not def or def.Active ~= true then
		return { ok = false, error = "Unknown building" }
	end
	local variant = request.Variant
	if type(variant) ~= "string" or not table.find(def.Variants, variant) then
		variant = def.Variants[1]
	end
	local rotation = GridMath.normalizeRotation(type(request.Rotation) == "number" and request.Rotation or 0)

	local ctx = {
		plot = bounds,
		buildingRects = BuildingService.getBuildingRects(player),
		roadCells = services.RoadService.getRoadCells(player),
	}
	local ok, reason, info = PlacementRules.validateBuilding(def, request.X, request.Z, rotation, ctx)
	if not ok then
		return { ok = false, error = reason }
	end

	local id = "B" .. tostring(country.NextBuildingId)
	country.NextBuildingId += 1
	local record = {
		Id = id,
		Type = def.Id,
		Variant = variant,
		X = info.centerX - bounds.minX,
		Z = info.centerZ - bounds.minZ,
		Rotation = rotation,
		State = Constants.BuildState.Planned,
		PlannedElapsed = 0,
		Progress = 0,
		CreatedAt = os.time(),
	}
	country.Buildings[id] = record
	local model = spawnModel(player, record)
	if model then
		services.ConstructionService.track(player, record, model)
	end
	services.DataService.markDirty(player)
	services.CountryService.push(player)
	return { ok = true, buildingId = id }
end

function BuildingService.init(allServices)
	services = allServices
	remotes = allServices.Remotes
end

function BuildingService.start()
	remotes[Constants.Remotes.PlaceBuilding].OnServerInvoke = handlePlace
	Players.PlayerRemoving:Connect(function(player)
		BuildingService.clearPlayer(player)
		lastRequest[player] = nil
	end)
end

return BuildingService
