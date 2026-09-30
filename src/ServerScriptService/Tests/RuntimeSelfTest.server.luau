-- RuntimeSelfTest: runs automatically in Studio Play (server side) and prints PASS/FAIL.
-- It exercises the REAL shared modules inside Roblox (registry, defaults, placement, road graph,
-- population). Result is also written to ReplicatedStorage attribute "WarStateSelfTest".

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

if not RunService:IsStudio() then
	return
end

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Modules = Shared:WaitForChild("Modules")
local Config = Shared:WaitForChild("Config")
local Countries = require(Modules:WaitForChild("Countries"))
local DefaultCountry = require(Modules:WaitForChild("DefaultCountry"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local RoadGraph = require(Modules:WaitForChild("RoadGraph"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local Plots = require(Modules:WaitForChild("Plots"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local Registry = require(Config:WaitForChild("CountryRegistry"))

local results = { passed = 0, failed = 0, failures = {} }

local function check(name: string, condition: boolean, detail: string?)
	if condition then
		results.passed += 1
	else
		results.failed += 1
		table.insert(results.failures, name .. (detail and (" (" .. detail .. ")") or ""))
	end
end

-- Registry
check("Registry has 195 countries", Countries.count() == 195, tostring(Countries.count()))
local seen, duplicates = {}, 0
for _, entry in ipairs(Countries.List) do
	if seen[entry.Id] then
		duplicates += 1
	end
	seen[entry.Id] = true
end
check("No duplicate country ids", duplicates == 0, tostring(duplicates))
for continent, expected in pairs(Registry.ExpectedContinentCounts) do
	local actual = #Countries.forContinent(continent)
	check("Continent count " .. continent, actual == expected, tostring(actual))
end
check("Holy See present", Countries.get("VA") ~= nil)
check("Palestine present", Countries.get("PS") ~= nil)

-- Empty country defaults
local country = DefaultCountry.new(1, "Novaria", "DE", "Europe", "USSR")
for _, key in ipairs({ "Money", "Oil", "Fuel", "Steel", "Supplies", "Population", "Workers", "HousingCapacity" }) do
	check("Empty country " .. key .. " = 0", country[key] == 0, tostring(country[key]))
end
check("Empty country has no buildings", next(country.Buildings) == nil)
check("Empty country has no roads", next(country.Roads) == nil)
check("Empty country has no military", next(country.Military) == nil)
for key in pairs(country) do
	check("No doctrine field: " .. key, not string.find(string.lower(key), "doctrine", 1, true))
end

-- Placement rules
local plot = Plots.getBounds(1)
local small
for _, def in ipairs(BuildingConfig.Buildings) do
	if def.Id == "SmallHouse" then
		small = def
	end
end
check("SmallHouse config exists", small ~= nil)
if small then
	local empty = { plot = plot, buildingRects = {}, roadCells = {} }
	local ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 96, 0, empty)
	check("House without roads is invalid", not ok and reason == PlacementRules.Reasons.NoRoads, reason)

	local roadOk, _, roadInfo = PlacementRules.validateRoad(plot.minX + 84, plot.minZ + 84, empty)
	check("Road inside territory is valid", roadOk)
	local ctx = {
		plot = plot,
		buildingRects = {},
		roadCells = { [GridMath.cellKey(roadInfo.ix, roadInfo.iz)] = roadInfo.rect },
	}
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 96, 0, ctx)
	check("House next to road is valid", ok, reason)
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 160, 0, ctx)
	check("House far from road is invalid", not ok and reason == PlacementRules.Reasons.TooFarFromRoad, reason)
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 84, 0, ctx)
	check("House on road is invalid", not ok and reason == PlacementRules.Reasons.OverlapRoad, reason)
	ok, reason = PlacementRules.validateBuilding(small, plot.minX - 50, plot.minZ + 84, 0, ctx)
	check("House outside territory is invalid", not ok and reason == PlacementRules.Reasons.OutsideTerritory, reason)
	local _, _, houseInfo = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 96, 0, ctx)
	ctx.buildingRects = { houseInfo.rect }
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 86, plot.minZ + 98, 0, ctx)
	check("Overlapping houses are invalid", not ok and reason == PlacementRules.Reasons.OverlapBuilding, reason)
	roadOk = PlacementRules.validateRoad(plot.minX + 84, plot.minZ + 84, ctx)
	check("Duplicate road is invalid", not roadOk)
end

-- Road graph
local cells = {}
local a = { RoadId = "A", Type = "Straight", Rotation = 0, Ix = 0, Iz = 0 }
local b = { RoadId = "B", Type = "Straight", Rotation = 0, Ix = 0, Iz = 1 }
local c = { RoadId = "C", Type = "Straight", Rotation = 0, Ix = 1, Iz = 0 }
cells[GridMath.cellKey(0, 0)] = a
cells[GridMath.cellKey(0, 1)] = b
cells[GridMath.cellKey(1, 0)] = c
RoadGraph.recomputeAll(cells)
check("Straight N-S segments connect", a.Connected and table.find(a.Neighbours, "B") ~= nil)
check("Side-by-side straights do not connect", table.find(a.Neighbours, "C") == nil and table.find(a.Adjacent, "C") ~= nil)
check("Rotation maps N->E", GridMath.rotateDirection("N", 1) == "E")
local cross = RoadGraph.openings("Crossroad", 0)
check("Crossroad has 4 openings", cross.N and cross.E and cross.S and cross.W)

-- Population
local PopulationService = require(script.Parent.Parent:WaitForChild("Systems"):WaitForChild("Population"):WaitForChild("PopulationService"))
local popCountry = DefaultCountry.new(1, "Test", "DE", "Europe", "USA")
PopulationService.recalculate(popCountry)
check("No population without housing", popCountry.Population == 0 and popCountry.HousingCapacity == 0)
popCountry.Buildings.B1 = { Id = "B1", Type = "SmallHouse", State = "COMPLETED" }
PopulationService.recalculate(popCountry)
for _ = 1, 50 do
	PopulationService.grow(popCountry)
end
check("Population capped by housing", popCountry.Population == popCountry.HousingCapacity and popCountry.HousingCapacity > 0)

local status = results.failed == 0 and "PASS" or "FAIL"
ReplicatedStorage:SetAttribute("WarStateSelfTest", string.format("%s %d/%d", status, results.passed, results.passed + results.failed))
if results.failed == 0 then
	print(string.format("[WarState SelfTest] PASS (%d checks)", results.passed))
else
	warn(string.format("[WarState SelfTest] FAIL (%d passed, %d failed)", results.passed, results.failed))
	for _, failure in ipairs(results.failures) do
		warn("  - " .. failure)
	end
end
