-- PlacementRules: shared placement validation.
-- The client uses it for the live preview, the SERVER uses the same rules as the authority.
--
-- ctx = {
--   plot = Plots bounds,
--   buildingRects = { Rect, ... },        -- world-space footprints of existing buildings
--   roadCells = { ["ix:iz"] = Rect, ... } -- world-space rects of existing road tiles
-- }

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local GridMath = require(Shared:WaitForChild("Modules"):WaitForChild("GridMath"))

local PlacementRules = {}

PlacementRules.Reasons = {
	Ok = "OK",
	OutsideTerritory = "Outside territory",
	OverlapBuilding = "Overlaps a building",
	OverlapRoad = "Overlaps a road",
	RoadOccupied = "Road already here",
	TooFarFromRoad = "Too far from road",
	NoRoads = "Build a road first",
	UnknownType = "Unknown type",
}

function PlacementRules.plotRect(plot)
	return { minX = plot.minX, maxX = plot.maxX, minZ = plot.minZ, maxZ = plot.maxZ }
end

-- Snap a world point to a building footprint. Returns centerX, centerZ, rect, width, depth.
function PlacementRules.snapBuilding(def, worldX: number, worldZ: number, rotation: number, plot)
	local width, depth = GridMath.rotatedSize(def.Footprint[1], def.Footprint[2], rotation)
	local cx, cz =
		GridMath.snapFootprint(worldX, worldZ, width, depth, PlacementConfig.GridSize, plot.minX, plot.minZ)
	return cx, cz, GridMath.rect(cx, cz, width, depth), width, depth
end

-- Snap a world point to a road tile. Returns ix, iz, centerX, centerZ, rect.
function PlacementRules.snapRoad(worldX: number, worldZ: number, plot)
	local size = PlacementConfig.RoadTileSize
	local ix = GridMath.cellIndex(worldX, size, plot.minX)
	local iz = GridMath.cellIndex(worldZ, size, plot.minZ)
	return ix, iz, PlacementRules.roadCellCenter(ix, iz, plot)
end

function PlacementRules.roadCellCenter(ix: number, iz: number, plot)
	local size = PlacementConfig.RoadTileSize
	local cx = GridMath.cellCenter(ix, size, plot.minX)
	local cz = GridMath.cellCenter(iz, size, plot.minZ)
	return cx, cz, GridMath.rect(cx, cz, size, size)
end

-- Distance from a point to the nearest road tile. Returns math.huge when no roads exist.
function PlacementRules.nearestRoadDistance(x: number, z: number, roadCells): number
	local best = math.huge
	for _, rect in pairs(roadCells) do
		local d = GridMath.pointRectDistance(x, z, rect)
		if d < best then
			best = d
		end
	end
	return best
end

-- Returns ok, reason, info
function PlacementRules.validateBuilding(def, worldX: number, worldZ: number, rotation: number, ctx)
	if not def then
		return false, PlacementRules.Reasons.UnknownType, nil
	end
	local tol = PlacementConfig.OverlapTolerance
	local cx, cz, rect = PlacementRules.snapBuilding(def, worldX, worldZ, rotation, ctx.plot)
	local info = { centerX = cx, centerZ = cz, rect = rect, roadDistance = math.huge }

	if not GridMath.rectInside(rect, PlacementRules.plotRect(ctx.plot), tol) then
		return false, PlacementRules.Reasons.OutsideTerritory, info
	end
	for _, other in ipairs(ctx.buildingRects) do
		if GridMath.rectsOverlap(rect, other, tol) then
			return false, PlacementRules.Reasons.OverlapBuilding, info
		end
	end
	for _, roadRect in pairs(ctx.roadCells) do
		if GridMath.rectsOverlap(rect, roadRect, tol) then
			return false, PlacementRules.Reasons.OverlapRoad, info
		end
	end
	if PlacementConfig.RequireRoadAccess then
		if next(ctx.roadCells) == nil then
			return false, PlacementRules.Reasons.NoRoads, info
		end
		local distance = PlacementRules.nearestRoadDistance(cx, cz, ctx.roadCells)
		info.roadDistance = distance
		if distance > PlacementConfig.MaxRoadDistance then
			return false, PlacementRules.Reasons.TooFarFromRoad, info
		end
	end
	return true, PlacementRules.Reasons.Ok, info
end

function PlacementRules.validateRoad(worldX: number, worldZ: number, ctx)
	local tol = PlacementConfig.OverlapTolerance
	local ix, iz, cx, cz, rect = PlacementRules.snapRoad(worldX, worldZ, ctx.plot)
	local info = { ix = ix, iz = iz, centerX = cx, centerZ = cz, rect = rect }
	if not GridMath.rectInside(rect, PlacementRules.plotRect(ctx.plot), tol) then
		return false, PlacementRules.Reasons.OutsideTerritory, info
	end
	if ctx.roadCells[GridMath.cellKey(ix, iz)] then
		return false, PlacementRules.Reasons.RoadOccupied, info
	end
	for _, other in ipairs(ctx.buildingRects) do
		if GridMath.rectsOverlap(rect, other, tol) then
			return false, PlacementRules.Reasons.OverlapBuilding, info
		end
	end
	return true, PlacementRules.Reasons.Ok, info
end

return PlacementRules
