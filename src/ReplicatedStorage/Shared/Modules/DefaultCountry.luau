-- DefaultCountry: creates an EMPTY country from GameConfig.EmptyCountry.
-- No starting resources, citizens, houses, roads or economy.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))

local DefaultCountry = {}

local function deepCopy(value)
	if type(value) ~= "table" then
		return value
	end
	local copy = {}
	for k, v in pairs(value) do
		copy[k] = deepCopy(v)
	end
	return copy
end

DefaultCountry.deepCopy = deepCopy

function DefaultCountry.new(slotIndex: number, name: string, flagId: string, continent: string, technologyBranch: string)
	local country = deepCopy(GameConfig.EmptyCountry)
	country.SchemaVersion = GameConfig.SchemaVersion
	country.SlotIndex = slotIndex
	country.Name = name
	country.FlagId = flagId
	country.Continent = continent
	country.TechnologyBranch = technologyBranch
	country.CreatedAt = os.time()
	country.NextBuildingId = 1
	country.NextRoadId = 1
	return country
end

-- Fill missing fields for older saves without granting anything.
function DefaultCountry.migrate(country)
	for key, value in pairs(GameConfig.EmptyCountry) do
		if country[key] == nil then
			country[key] = deepCopy(value)
		end
	end
	country.NextBuildingId = country.NextBuildingId or 1
	country.NextRoadId = country.NextRoadId or 1
	country.SchemaVersion = GameConfig.SchemaVersion
	return country
end

return DefaultCountry
