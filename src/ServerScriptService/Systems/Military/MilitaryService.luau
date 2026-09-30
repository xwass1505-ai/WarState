-- MilitaryService: PLANNED placeholder.
-- Future military layer (units, military UI/data). No combat or weapons are implemented.
-- This module intentionally contains NO gameplay mechanics. It only reserves the interface.

local MilitaryService = {}
MilitaryService.Name = "MilitaryService"
MilitaryService.Status = "PLANNED"
MilitaryService.Active = false
MilitaryService.Description = "Future military layer (units, military UI/data). No combat or weapons are implemented."

function MilitaryService.init(_services) end

function MilitaryService.start() end

return MilitaryService
