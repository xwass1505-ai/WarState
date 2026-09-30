-- ProductionService: PLANNED placeholder.
-- Production chains (Oil Well -> Crude Oil -> Refinery -> Fuel). Requires stable road graph and logistics.
-- This module intentionally contains NO gameplay mechanics. It only reserves the interface.

local ProductionService = {}
ProductionService.Name = "ProductionService"
ProductionService.Status = "PLANNED"
ProductionService.Active = false
ProductionService.Description = "Production chains (Oil Well -> Crude Oil -> Refinery -> Fuel). Requires stable road graph and logistics."

function ProductionService.init(_services) end

function ProductionService.start() end

return ProductionService
