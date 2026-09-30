-- RoadModels: procedural road tiles (Straight, Corner, TJunction, Crossroad).
-- Tiles are built unrotated (openings from RoadConfig) and rotated by the caller with GridMath.yawForRotation.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local RoadConfig = require(Shared:WaitForChild("Config"):WaitForChild("RoadConfig"))

local RoadModels = {}

local function rgb(t)
	return Color3.fromRGB(t[1], t[2], t[3])
end

local SIDEWALK = rgb(RoadConfig.Colors.Sidewalk)
local ASPHALT = rgb(RoadConfig.Colors.Asphalt)
local MARKING = rgb(RoadConfig.Colors.Marking)

local function part(model, name, size, position, color)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = CFrame.new(position)
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p:SetAttribute("BaseTransparency", 0)
	p.Parent = model
	return p
end

local ARM = {
	N = { 0, -1 },
	E = { 1, 0 },
	S = { 0, 1 },
	W = { -1, 0 },
}

function RoadModels.build(typeId: string)
	local roadType
	for _, t in ipairs(RoadConfig.Types) do
		if t.Id == typeId then
			roadType = t
		end
	end
	assert(roadType, "Unknown road type " .. tostring(typeId))

	local size = RoadConfig.TileSize
	local half = size / 2
	local lane = RoadConfig.RoadWidth
	local model = Instance.new("Model")
	model.Name = "Road_" .. typeId

	local root = part(model, "Root", Vector3.new(size, 0.2, size), Vector3.new(0, 0, 0), SIDEWALK)
	root.Transparency = 1
	root:SetAttribute("BaseTransparency", 1)
	model.PrimaryPart = root

	part(model, "Sidewalk", Vector3.new(size, 0.2, size), Vector3.new(0, 0.1, 0), SIDEWALK)
	part(model, "Asphalt", Vector3.new(lane, 0.24, lane), Vector3.new(0, 0.12, 0), ASPHALT)

	local edge = (size - lane) / 2
	for _, dir in ipairs(roadType.Openings) do
		local o = ARM[dir]
		local armCenter = half - edge / 2
		local armSize
		if o[1] == 0 then
			armSize = Vector3.new(lane, 0.24, edge)
		else
			armSize = Vector3.new(edge, 0.24, lane)
		end
		part(model, "Arm" .. dir, armSize, Vector3.new(o[1] * armCenter, 0.12, o[2] * armCenter), ASPHALT)
		-- Lane dash on each open arm (subtle, flat)
		local dashCenter = half * 0.55
		local dashSize
		if o[1] == 0 then
			dashSize = Vector3.new(0.25, 0.04, 1.3)
		else
			dashSize = Vector3.new(1.3, 0.04, 0.25)
		end
		part(model, "Dash" .. dir, dashSize, Vector3.new(o[1] * dashCenter, 0.25, o[2] * dashCenter), MARKING)
	end
	return model
end

return RoadModels
