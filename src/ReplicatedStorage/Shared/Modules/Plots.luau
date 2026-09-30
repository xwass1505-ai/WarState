-- Plots: territory geometry. Each active country gets one flat plot (territory).
-- Building and road positions are saved in plot-LOCAL coordinates so a country can
-- be loaded onto any free plot in a later session.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))

local Plots = {}

function Plots.getBounds(index: number)
	local t = GameConfig.Territory
	local centerX = t.OriginX + (index - 1) * t.Spacing
	local centerZ = t.OriginZ
	local half = t.Size / 2
	return {
		index = index,
		centerX = centerX,
		centerZ = centerZ,
		minX = centerX - half,
		maxX = centerX + half,
		minZ = centerZ - half,
		maxZ = centerZ + half,
		size = t.Size,
		surfaceY = t.SurfaceY,
	}
end

function Plots.toWorld(bounds, localX: number, localZ: number): (number, number)
	return bounds.minX + localX, bounds.minZ + localZ
end

function Plots.toLocal(bounds, worldX: number, worldZ: number): (number, number)
	return worldX - bounds.minX, worldZ - bounds.minZ
end

function Plots.maxPlots(): number
	return GameConfig.Territory.MaxPlots
end

return Plots
