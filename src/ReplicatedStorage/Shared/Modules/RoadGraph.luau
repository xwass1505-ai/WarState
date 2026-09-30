-- RoadGraph: pure road-network logic (no Instances).
-- Segment record fields (saved): RoadId, Type, Rotation, Ix, Iz, Position {X, Z} (plot-local)
-- Derived fields (recomputed): Neighbours (connected RoadIds), Adjacent (touching RoadIds), Connected
-- The graph is ready for future pathfinding: Neighbours are true bidirectional edges.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local RoadConfig = require(Shared:WaitForChild("Config"):WaitForChild("RoadConfig"))
local GridMath = require(Shared:WaitForChild("Modules"):WaitForChild("GridMath"))

local RoadGraph = {}

local typeById = {}
for _, roadType in ipairs(RoadConfig.Types) do
	typeById[roadType.Id] = roadType
end

function RoadGraph.getType(typeId: string)
	return typeById[typeId]
end

-- Returns a set {N=true, ...} of open sides after rotation.
function RoadGraph.openings(typeId: string, rotation: number)
	local roadType = typeById[typeId]
	local result = {}
	if not roadType then
		return result
	end
	for _, dir in ipairs(roadType.Openings) do
		result[GridMath.rotateDirection(dir, rotation)] = true
	end
	return result
end

-- segmentsByCell: map "ix:iz" -> segment
local function refreshSegment(segmentsByCell, segment)
	local open = RoadGraph.openings(segment.Type, segment.Rotation)
	local neighbours = {}
	local adjacent = {}
	for _, dir in ipairs(GridMath.DirectionOrder) do
		local offset = GridMath.DirectionOffset[dir]
		local other = segmentsByCell[GridMath.cellKey(segment.Ix + offset[1], segment.Iz + offset[2])]
		if other then
			table.insert(adjacent, other.RoadId)
			local otherOpen = RoadGraph.openings(other.Type, other.Rotation)
			if open[dir] and otherOpen[GridMath.Opposite[dir]] then
				table.insert(neighbours, other.RoadId)
			end
		end
	end
	segment.Neighbours = neighbours
	segment.Adjacent = adjacent
	segment.Connected = #neighbours > 0
end

-- Recompute a segment and its four adjacent cells after a change.
function RoadGraph.updateAround(segmentsByCell, ix: number, iz: number)
	local center = segmentsByCell[GridMath.cellKey(ix, iz)]
	if center then
		refreshSegment(segmentsByCell, center)
	end
	for _, dir in ipairs(GridMath.DirectionOrder) do
		local offset = GridMath.DirectionOffset[dir]
		local other = segmentsByCell[GridMath.cellKey(ix + offset[1], iz + offset[2])]
		if other then
			refreshSegment(segmentsByCell, other)
		end
	end
end

function RoadGraph.recomputeAll(segmentsByCell)
	for _, segment in pairs(segmentsByCell) do
		refreshSegment(segmentsByCell, segment)
	end
end

-- Breadth-first count of the network reachable from a RoadId (future logistics/pathfinding hook).
function RoadGraph.networkSize(segmentsById, startId: string): number
	local visited = { [startId] = true }
	local queue = { startId }
	local count = 0
	while #queue > 0 do
		local id = table.remove(queue, 1)
		local segment = segmentsById[id]
		if segment then
			count += 1
			for _, n in ipairs(segment.Neighbours or {}) do
				if not visited[n] then
					visited[n] = true
					table.insert(queue, n)
				end
			end
		end
	end
	return count
end

return RoadGraph
