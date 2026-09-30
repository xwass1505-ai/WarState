-- ResearchService: PLANNED placeholder.
-- Time-based research (ResearchTime, Requirements, Unlocks). Not active in the initial bootstrap.
-- This module intentionally contains NO gameplay mechanics. It only reserves the interface.

local ResearchService = {}
ResearchService.Name = "ResearchService"
ResearchService.Status = "PLANNED"
ResearchService.Active = false
ResearchService.Description = "Time-based research (ResearchTime, Requirements, Unlocks). Not active in the initial bootstrap."

function ResearchService.init(_services) end

function ResearchService.start() end

return ResearchService
