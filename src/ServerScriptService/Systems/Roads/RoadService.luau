-- RoadService: server-authoritative road placement and the road graph.
-- Roads snap to the RoadTileSize grid, connect to adjacent segments and form a network
-- (RoadGraph) that future traffic/logistics/pathfinding will use.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local Modules = Shared:WaitForChild("Modules")
local RoadConfig = require(Config:WaitForChild("RoadConfig"))
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local RoadGraph = require(Modules:WaitForChild("RoadGraph"))
local RoadModels = require(Modules:WaitForChild("RoadModels"))

local RoadService = {}
RoadService.Name = "RoadService"

local services
local remotes
local runtime = {} -- [Player] = { cells = {key -> segment}, models = {RoadId -> Model} }
local lastRequest = {}

local function getRuntime(player)
	local r = runtime[player]
	if not r then
		r = { cells = {}, models = {} }
		runtime[player] = r
	end
	return r
end

local function spawnModel(player, segment)
	local folder = services.WorldService.getPlotFolder(player, "Roads")
	local bounds = services.WorldService.getBounds(player)
	if not folder or not bounds then
		return
	end
	local r = getRuntime(player)
	local old = r.models[segment.RoadId]
	if old then
		old:Destroy()
	end
	local model = RoadModels.build(segment.Type)
	model.Name = segment.RoadId
	local wx, wz = bounds.minX + segment.Position.X, bounds.minZ + segment.Position.Z
	model:PivotTo(CFrame.new(wx, bounds.surfaceY, wz) * CFrame.Angles(0, GridMath.yawForRotation(segment.Rotation), 0))
	local size = PlacementConfig.RoadTileSize
	model:SetAttribute(Constants.Attributes.Kind, "Road")
	model:SetAttribute(Constants.Attributes.TypeId, segment.Type)
	model:SetAttribute("Ix", segment.Ix)
	model:SetAttribute("Iz", segment.Iz)
	model:SetAttribute("Rotation", segment.Rotation)
	model:SetAttribute("RectMinX", wx - size / 2)
	model:SetAttribute("RectMaxX", wx + size / 2)
	model:SetAttribute("RectMinZ", wz - size / 2)
	model:SetAttribute("RectMaxZ", wz + size / 2)
	model:SetAttribute("Connected", segment.Connected == true)
	model.Parent = folder
	r.models[segment.RoadId] = model
end

local function refreshAttributes(player)
	local r = runtime[player]
	if not r then
		return
	end
	for _, segment in pairs(r.cells) do
		local model = r.models[segment.RoadId]
		if model then
			model:SetAttribute("Connected", segment.Connected == true)
		end
	end
end

-- World-space rects of all road tiles, keyed by cell (used by placement validation).
function RoadService.getRoadCells(player: Player)
	local result = {}
	local r = runtime[player]
	local bounds = services.WorldService.getBounds(player)
	if not r or not bounds then
		return result
	end
	for key, segment in pairs(r.cells) do
		local _, _, rect = PlacementRules.roadCellCenter(segment.Ix, segment.Iz, bounds)
		result[key] = rect
	end
	return result
end

function RoadService.getSegments(player: Player)
	local r = runtime[player]
	return r and r.cells or {}
end

function RoadService.loadCountry(player: Player, country)
	RoadService.clearPlayer(player)
	local r = getRuntime(player)
	for _, segment in pairs(country.Roads) do
		r.cells[GridMath.cellKey(segment.Ix, segment.Iz)] = segment
	end
	RoadGraph.recomputeAll(r.cells)
	for _, segment in pairs(r.cells) do
		spawnModel(player, segment)
	end
end

function RoadService.clearPlayer(player: Player)
	local r = runtime[player]
	if r then
		for _, model in pairs(r.models) do
			model:Destroy()
		end
	end
	runtime[player] = nil
end

local function typeIsActive(typeId)
	for _, t in ipairs(RoadConfig.Types) do
		if t.Id == typeId then
			return t.Active == true
		end
	end
	return false
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
	if type(request.Type) ~= "string" or not typeIsActive(request.Type) then
		return { ok = false, error = "Unknown road type" }
	end
	local rotation = GridMath.normalizeRotation(type(request.Rotation) == "number" and request.Rotation or 0)

	local ctx = {
		plot = bounds,
		buildingRects = services.BuildingService.getBuildingRects(player),
		roadCells = RoadService.getRoadCells(player),
	}
	local ok, reason, info = PlacementRules.validateRoad(request.X, request.Z, ctx)
	if not ok then
		return { ok = false, error = reason }
	end

	local r = getRuntime(player)
	local roadId = "R" .. tostring(country.NextRoadId)
	country.NextRoadId += 1
	local segment = {
		RoadId = roadId,
		Type = request.Type,
		Rotation = rotation,
		Ix = info.ix,
		Iz = info.iz,
		Position = { X = info.centerX - bounds.minX, Z = info.centerZ - bounds.minZ },
		Neighbours = {},
		Adjacent = {},
		Connected = false,
	}
	country.Roads[roadId] = segment
	r.cells[GridMath.cellKey(info.ix, info.iz)] = segment
	RoadGraph.updateAround(r.cells, info.ix, info.iz)
	spawnModel(player, segment)
	refreshAttributes(player)
	services.DataService.markDirty(player)
	services.CountryService.push(player)
	return { ok = true, roadId = roadId, connected = segment.Connected }
end

function RoadService.init(allServices)
	services = allServices
	remotes = allServices.Remotes
end

function RoadService.start()
	remotes[Constants.Remotes.PlaceRoad].OnServerInvoke = handlePlace
	Players.PlayerRemoving:Connect(function(player)
		RoadService.clearPlayer(player)
		lastRequest[player] = nil
	end)
end

return RoadService
