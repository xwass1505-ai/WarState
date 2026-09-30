-- PopulationService: logical population (no physical NPCs).
-- Completed housing -> HousingCapacity -> Population grows gradually, never above HousingCapacity.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))

local PopulationService = {}
PopulationService.Name = "PopulationService"

local services
local capacityByType = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	capacityByType[def.Id] = def.HousingCapacity or 0
end

function PopulationService.capacityOf(country): number
	local capacity = 0
	for _, record in pairs(country.Buildings) do
		if record.State == Constants.BuildState.Completed then
			capacity += capacityByType[record.Type] or 0
		end
	end
	return capacity
end

-- Recalculate capacity and clamp population (called on load and when housing completes).
function PopulationService.recalculate(country)
	country.HousingCapacity = PopulationService.capacityOf(country)
	if country.Population > country.HousingCapacity then
		country.Population = country.HousingCapacity
	end
	country.Workers = math.floor(country.Population * GameConfig.Population.WorkerRatio)
end

-- One growth step. Returns true if population changed.
function PopulationService.grow(country): boolean
	local capacity = country.HousingCapacity
	local population = country.Population
	if population >= capacity then
		if population > capacity then
			country.Population = capacity
			return true
		end
		return false
	end
	local free = capacity - population
	local growth = math.max(GameConfig.Population.MinGrowth, math.floor(free * GameConfig.Population.GrowthFraction))
	country.Population = math.min(capacity, population + growth)
	country.Workers = math.floor(country.Population * GameConfig.Population.WorkerRatio)
	return true
end

function PopulationService.init(allServices)
	services = allServices
end

function PopulationService.start()
	task.spawn(function()
		while true do
			task.wait(GameConfig.Population.TickSeconds)
			for _, player in ipairs(game:GetService("Players"):GetPlayers()) do
				local country = services.DataService.getCountry(player)
				if country and PopulationService.grow(country) then
					services.DataService.markDirty(player)
					services.CountryService.push(player)
				end
			end
		end
	end)
end

return PopulationService
