-- ResourceService: PARTIAL.
-- Resources (Money, Oil, Fuel, Steel, Supplies) exist in country data and are replicated,
-- but they stay at ZERO and are INACTIVE in the current build. No starting resources are granted.
-- Future: Oil Well -> Crude Oil -> Refinery -> Fuel, Factory -> Road -> Truck -> Warehouse.

local ResourceService = {}
ResourceService.Name = "ResourceService"
ResourceService.Status = "PARTIAL"
ResourceService.ResourceKeys = { "Money", "Oil", "Fuel", "Steel", "Supplies" }
ResourceService.Active = false

local services

function ResourceService.get(player: Player)
	local country = services.DataService.getCountry(player)
	if not country then
		return nil
	end
	local result = {}
	for _, key in ipairs(ResourceService.ResourceKeys) do
		result[key] = country[key] or 0
	end
	return result
end

function ResourceService.init(allServices)
	services = allServices
end

function ResourceService.start() end

return ResourceService
