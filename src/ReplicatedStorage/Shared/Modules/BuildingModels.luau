-- BuildingModels: procedural low-poly building visuals (no external assets needed).
-- Every model is built around a ground-level invisible Root part (PrimaryPart) and faces +Z at rotation 0.
-- Visual parts do NOT collide (CanCollide=false). Placement validation is a separate system.

local BuildingModels = {}

local RAD45 = math.rad(45)
local RAD90 = math.rad(90)

local C = {
	Cream = Color3.fromRGB(241, 231, 210),
	Beige = Color3.fromRGB(226, 208, 180),
	White = Color3.fromRGB(244, 244, 240),
	Sky = Color3.fromRGB(196, 218, 238),
	Sage = Color3.fromRGB(178, 199, 166),
	Sand = Color3.fromRGB(222, 196, 158),
	Brick = Color3.fromRGB(176, 98, 78),
	Terracotta = Color3.fromRGB(193, 108, 82),
	Slate = Color3.fromRGB(86, 98, 114),
	Charcoal = Color3.fromRGB(70, 74, 82),
	RoofBrown = Color3.fromRGB(122, 86, 64),
	Wood = Color3.fromRGB(158, 114, 78),
	Door = Color3.fromRGB(104, 76, 58),
	Glass = Color3.fromRGB(164, 202, 230),
	Foundation = Color3.fromRGB(182, 182, 176),
	Trim = Color3.fromRGB(250, 250, 248),
	Green = Color3.fromRGB(110, 150, 96),
}
BuildingModels.Palette = C

local function part(model, name, size, cframe, color, material, transparency)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = cframe
	p.Color = color
	p.Material = material or Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Transparency = transparency or 0
	p:SetAttribute("BaseTransparency", p.Transparency)
	p.Parent = model
	return p
end

local function box(model, name, sx, sy, sz, x, y, z, color, material)
	return part(model, name, Vector3.new(sx, sy, sz), CFrame.new(x, y, z), color, material)
end

-- Gable roof. Ridge runs along world X when ridgeAlongX is true, else along world Z.
-- (bx, bz) = body center, w/d = body size in world X/Z, h = wall height.
local function gableRoof(model, bx, bz, w, d, h, ridgeAlongX, wallColor, roofColor)
	local frame = CFrame.new(bx, 0, bz)
	local length, span = w, d
	if not ridgeAlongX then
		frame = frame * CFrame.Angles(0, RAD90, 0)
		length, span = d, w
	end
	local s = span / 2
	local side = span / math.sqrt(2)
	local overhang = 0.5
	local t = 0.3
	-- Triangular gable: a 45-degree rotated square prism; its lower half is hidden inside the body/ground.
	part(model, "Gable", Vector3.new(length, side, side), frame * CFrame.new(0, h, 0) * CFrame.Angles(RAD45, 0, 0), wallColor)
	local slabLength = s * math.sqrt(2) + overhang
	local slabSize = Vector3.new(length + 0.5, t, slabLength)
	part(
		model,
		"RoofA",
		slabSize,
		frame * CFrame.new(0, h + s / 2, s / 2) * CFrame.Angles(RAD45, 0, 0) * CFrame.new(0, t / 2, overhang / 2),
		roofColor
	)
	part(
		model,
		"RoofB",
		slabSize,
		frame * CFrame.new(0, h + s / 2, -s / 2) * CFrame.Angles(-RAD45, 0, 0) * CFrame.new(0, t / 2, -overhang / 2),
		roofColor
	)
	part(model, "Ridge", Vector3.new(length + 0.6, 0.3, 0.45), frame * CFrame.new(0, h + s + 0.12, 0), roofColor:Lerp(Color3.new(0, 0, 0), 0.15))
	return h + s
end

local function flatRoof(model, bx, bz, w, d, h, roofColor, trimColor)
	box(model, "RoofSlab", w + 0.4, 0.35, d + 0.4, bx, h + 0.175, bz, roofColor)
	box(model, "Parapet", w + 0.5, 0.2, d + 0.5, bx, h + 0.45, bz, trimColor)
	return h + 0.55
end

local function frontWindows(model, bx, bz, w, d, floors, count, skipCenter, glass)
	local faceZ = bz + d / 2 + 0.06
	for floor = 1, floors do
		local y = 2.0 + (floor - 1) * 3.2
		for i = 1, count do
			local fx = bx - w / 2 + (i - 0.5) * (w / count)
			local isCenter = math.abs(fx - bx) < w / count / 2
			if not (floor == 1 and skipCenter and isCenter) then
				box(model, "Window", 1.2, 1.2, 0.12, fx, y, faceZ, glass)
			end
		end
	end
end

local function sideWindows(model, bx, bz, w, d, floors, glass)
	for floor = 1, floors do
		local y = 2.0 + (floor - 1) * 3.2
		box(model, "WindowL", 0.12, 1.2, 1.2, bx - w / 2 - 0.06, y, bz, glass)
		box(model, "WindowR", 0.12, 1.2, 1.2, bx + w / 2 + 0.06, y, bz, glass)
	end
end

local function door(model, x, bz, d, color)
	box(model, "Door", 1.4, 2.5, 0.14, x, 0.3 + 1.25, bz + d / 2 + 0.07, color)
	box(model, "Step", 2.0, 0.2, 0.7, x, 0.1, bz + d / 2 + 0.35, C.Foundation)
end

local function foundation(model, bx, bz, w, d)
	box(model, "Foundation", w + 0.4, 0.3, d + 0.4, bx, 0.15, bz, C.Foundation)
end

local function body(model, name, bx, bz, w, d, h, color)
	return box(model, name, w, h - 0.3, d, bx, 0.3 + (h - 0.3) / 2, bz, color)
end

-- roofY = roof surface height at (x, z); the chimney base is sunk into the roof.
local function chimney(model, x, z, roofY, color)
	box(model, "Chimney", 0.8, 2.4, 0.8, x, roofY + 0.7, z, color)
end

local function floorBand(model, bx, bz, w, d, y, color)
	box(model, "Band", w + 0.1, 0.25, d + 0.1, bx, y, bz, color)
end

local function garage(model, bx, bz, w, d, h, wallColor, roofColor)
	body(model, "Garage", bx, bz, w, d, h, wallColor)
	box(model, "GarageDoor", w - 1.0, h - 1.2, 0.12, bx, 0.3 + (h - 1.2) / 2, bz + d / 2 + 0.06, C.Trim)
	box(model, "GarageRoof", w + 0.3, 0.3, d + 0.3, bx, h + 0.15, bz, roofColor)
end

local function porch(model, x, frontZ, width, depth, h, roofColor)
	box(model, "PorchDeck", width, 0.25, depth, x, 0.125, frontZ + depth / 2, C.Wood)
	box(model, "PorchPostL", 0.25, h, 0.25, x - width / 2 + 0.2, h / 2, frontZ + depth - 0.2, C.Trim)
	box(model, "PorchPostR", 0.25, h, 0.25, x + width / 2 - 0.2, h / 2, frontZ + depth - 0.2, C.Trim)
	box(model, "PorchRoof", width + 0.3, 0.25, depth + 0.2, x, h + 0.12, frontZ + depth / 2, roofColor)
end

local function shrub(model, x, z, size)
	box(model, "Shrub", size, size * 0.8, size, x, size * 0.4, z, C.Green)
end

-- Variant builders. Each receives the model and footprint (w, d) and must stay inside it.
local Variants = {}

-- SMALL HOUSES (8 x 8)
Variants.SmallHouse_A = function(m)
	foundation(m, 0, -0.4, 6.6, 5.8)
	body(m, "Body", 0, -0.4, 6.6, 5.8, 4.2, C.Cream)
	gableRoof(m, 0, -0.4, 6.6, 5.8, 4.2, true, C.Cream, C.Terracotta)
	chimney(m, 1.8, -1.6, 5.9, C.Brick)
	door(m, 0, -0.4, 5.8, C.Door)
	frontWindows(m, 0, -0.4, 6.6, 5.8, 1, 3, true, C.Glass)
	sideWindows(m, 0, -0.4, 6.6, 5.8, 1, C.Glass)
	shrub(m, -2.8, 3.2, 0.9)
end

Variants.SmallHouse_B = function(m)
	foundation(m, 0, -0.9, 6.0, 5.4)
	body(m, "Body", 0, -0.9, 6.0, 5.4, 4.0, C.Sky)
	gableRoof(m, 0, -0.9, 6.0, 5.4, 4.0, false, C.Sky, C.Slate)
	door(m, 0, -0.9, 5.4, C.Trim)
	frontWindows(m, 0, -0.9, 6.0, 5.4, 1, 2, false, C.Glass)
	porch(m, 0, -0.9 + 2.7, 3.2, 1.4, 2.8, C.Slate)
end

Variants.SmallHouse_C = function(m)
	foundation(m, 0, -0.3, 6.8, 6.0)
	body(m, "Body", 0, -0.3, 6.8, 6.0, 3.8, C.White)
	box(m, "Cladding", 2.2, 3.4, 0.1, -2.2, 0.3 + 1.7, -0.3 + 3.0 + 0.05, C.Wood)
	flatRoof(m, 0, -0.3, 6.8, 6.0, 3.8, C.Charcoal, C.White)
	box(m, "WideWindow", 3.2, 1.4, 0.12, 1.2, 2.2, -0.3 + 3.0 + 0.06, C.Glass)
	door(m, -2.2, -0.3, 6.0, C.Charcoal)
	sideWindows(m, 0, -0.3, 6.8, 6.0, 1, C.Glass)
end

Variants.SmallHouse_D = function(m)
	foundation(m, -0.7, -0.4, 5.4, 5.8)
	body(m, "Body", -0.7, -0.4, 5.4, 5.8, 4.4, C.Sage)
	gableRoof(m, -0.7, -0.4, 5.4, 5.8, 4.4, true, C.Sage, C.RoofBrown)
	door(m, -0.7, -0.4, 5.8, C.Door)
	frontWindows(m, -0.7, -0.4, 5.4, 5.8, 1, 3, true, C.Glass)
	box(m, "Shed", 1.8, 2.4, 3.0, 2.9, 1.2, -1.2, C.Wood)
	box(m, "ShedRoof", 2.1, 0.25, 3.3, 2.9, 2.5, -1.2, C.RoofBrown)
end

-- MEDIUM HOUSES (12 x 8)
Variants.MediumHouse_A = function(m)
	foundation(m, 0, -0.5, 10.4, 6.0)
	body(m, "Body", 0, -0.5, 10.4, 6.0, 7.0, C.Beige)
	floorBand(m, 0, -0.5, 10.4, 6.0, 3.6, C.Trim)
	gableRoof(m, 0, -0.5, 10.4, 6.0, 7.0, true, C.Beige, C.Slate)
	chimney(m, -3.4, -1.6, 8.9, C.Brick)
	door(m, 0, -0.5, 6.0, C.Door)
	frontWindows(m, 0, -0.5, 10.4, 6.0, 2, 4, true, C.Glass)
	sideWindows(m, 0, -0.5, 10.4, 6.0, 2, C.Glass)
end

Variants.MediumHouse_B = function(m)
	-- L-shape: main block + perpendicular wing
	foundation(m, -1.6, -1.0, 7.2, 5.4)
	body(m, "Body", -1.6, -1.0, 7.2, 5.4, 4.4, C.Cream)
	gableRoof(m, -1.6, -1.0, 7.2, 5.4, 4.4, true, C.Cream, C.Terracotta)
	foundation(m, 3.4, 0.0, 4.2, 7.4)
	body(m, "Wing", 3.4, 0.0, 4.2, 7.4, 4.4, C.Cream)
	gableRoof(m, 3.4, 0.0, 4.2, 7.4, 4.4, false, C.Cream, C.Terracotta)
	door(m, -1.6, -1.0, 5.4, C.Door)
	frontWindows(m, -1.6, -1.0, 7.2, 5.4, 1, 3, true, C.Glass)
	box(m, "WingWindow", 1.6, 1.3, 0.12, 3.4, 2.1, 3.76, C.Glass)
end

Variants.MediumHouse_C = function(m)
	-- Modern stacked boxes
	foundation(m, 0, -0.4, 10.6, 6.2)
	body(m, "Lower", 0, -0.4, 10.6, 6.2, 3.6, C.White)
	flatRoof(m, 0, -0.4, 10.6, 6.2, 3.6, C.Charcoal, C.White)
	box(m, "Upper", 6.0, 2.8, 5.0, -1.8, 3.95 + 1.4, -0.9, C.Sky)
	box(m, "UpperRoof", 6.4, 0.3, 5.4, -1.8, 3.95 + 2.95, -0.9, C.Charcoal)
	box(m, "UpperWindow", 3.6, 1.3, 0.12, -1.8, 5.4, -0.9 + 2.56, C.Glass)
	box(m, "Glazing", 4.0, 1.6, 0.12, 2.6, 2.1, -0.4 + 3.16, C.Glass)
	door(m, -2.0, -0.4, 6.2, C.Charcoal)
	sideWindows(m, 0, -0.4, 10.6, 6.2, 1, C.Glass)
end

Variants.MediumHouse_D = function(m)
	foundation(m, -1.5, -0.6, 7.6, 6.0)
	body(m, "Body", -1.5, -0.6, 7.6, 6.0, 4.4, C.Sand)
	gableRoof(m, -1.5, -0.6, 7.6, 6.0, 4.4, true, C.Sand, C.RoofBrown)
	door(m, -1.5, -0.6, 6.0, C.Door)
	frontWindows(m, -1.5, -0.6, 7.6, 6.0, 1, 3, true, C.Glass)
	garage(m, 4.1, -0.4, 3.4, 6.4, 3.4, C.Sand, C.RoofBrown)
end

-- LARGE HOUSES (16 x 12)
Variants.LargeHouse_A = function(m)
	foundation(m, -1.6, -0.8, 11.6, 8.4)
	body(m, "Body", -1.6, -0.8, 11.6, 8.4, 7.2, C.Cream)
	floorBand(m, -1.6, -0.8, 11.6, 8.4, 3.7, C.Trim)
	gableRoof(m, -1.6, -0.8, 11.6, 8.4, 7.2, true, C.Cream, C.Slate)
	chimney(m, 2.2, -2.8, 8.6, C.Brick)
	door(m, -1.6, -0.8, 8.4, C.Door)
	frontWindows(m, -1.6, -0.8, 11.6, 8.4, 2, 5, true, C.Glass)
	sideWindows(m, -1.6, -0.8, 11.6, 8.4, 2, C.Glass)
	garage(m, 5.9, -0.4, 3.6, 7.6, 3.6, C.Cream, C.Slate)
	shrub(m, -6.8, 4.6, 1.1)
end

Variants.LargeHouse_B = function(m)
	foundation(m, 0, -0.6, 14.4, 9.0)
	body(m, "Lower", 0, -0.6, 14.4, 9.0, 3.8, C.White)
	flatRoof(m, 0, -0.6, 14.4, 9.0, 3.8, C.Charcoal, C.White)
	box(m, "Upper", 8.6, 3.0, 7.0, 2.4, 4.15 + 1.5, -1.6, C.White)
	box(m, "UpperRoof", 9.0, 0.3, 7.4, 2.4, 4.15 + 3.15, -1.6, C.Charcoal)
	box(m, "UpperGlazing", 6.0, 1.6, 0.12, 2.4, 5.7, -1.6 + 3.56, C.Glass)
	box(m, "TerraceRail", 5.2, 0.6, 0.15, -4.4, 4.45, 3.7, C.Trim)
	box(m, "Glazing", 6.4, 1.8, 0.12, 3.2, 2.2, -0.6 + 4.56, C.Glass)
	box(m, "WoodPanel", 3.0, 3.2, 0.14, -4.8, 2.0, -0.6 + 4.57, C.Wood)
	door(m, -1.6, -0.6, 9.0, C.Charcoal)
	sideWindows(m, 0, -0.6, 14.4, 9.0, 1, C.Glass)
end

Variants.LargeHouse_C = function(m)
	-- Two-storey L-shape
	foundation(m, -2.0, -1.6, 10.8, 7.2)
	body(m, "Body", -2.0, -1.6, 10.8, 7.2, 7.0, C.Beige)
	floorBand(m, -2.0, -1.6, 10.8, 7.2, 3.6, C.Trim)
	gableRoof(m, -2.0, -1.6, 10.8, 7.2, 7.0, true, C.Beige, C.Terracotta)
	foundation(m, 4.6, 0.2, 5.4, 10.6)
	body(m, "Wing", 4.6, 0.2, 5.4, 10.6, 7.0, C.Beige)
	floorBand(m, 4.6, 0.2, 5.4, 10.6, 3.6, C.Trim)
	gableRoof(m, 4.6, 0.2, 5.4, 10.6, 7.0, false, C.Beige, C.Terracotta)
	door(m, -2.0, -1.6, 7.2, C.Door)
	frontWindows(m, -2.0, -1.6, 10.8, 7.2, 2, 4, true, C.Glass)
	frontWindows(m, 4.6, 0.2, 5.4, 10.6, 2, 2, false, C.Glass)
end

Variants.LargeHouse_D = function(m)
	foundation(m, 0, -1.2, 10.0, 8.6)
	body(m, "Body", 0, -1.2, 10.0, 8.6, 7.4, C.Sky)
	floorBand(m, 0, -1.2, 10.0, 8.6, 3.7, C.Trim)
	gableRoof(m, 0, -1.2, 10.0, 8.6, 7.4, false, C.Sky, C.Charcoal)
	chimney(m, -3.2, -3.0, 9.2, C.Brick)
	door(m, 0, -1.2, 8.6, C.Trim)
	frontWindows(m, 0, -1.2, 10.0, 8.6, 2, 4, true, C.Glass)
	sideWindows(m, 0, -1.2, 10.0, 8.6, 2, C.Glass)
	porch(m, 0, -1.2 + 4.3, 5.0, 1.6, 3.0, C.Charcoal)
	shrub(m, -5.8, 4.8, 1.0)
	shrub(m, 5.8, 4.8, 1.0)
end

BuildingModels.Variants = Variants

function BuildingModels.hasVariant(variantId: string): boolean
	return Variants[variantId] ~= nil
end

-- Builds the model at the origin. Caller positions it with model:PivotTo(cframe).
function BuildingModels.build(def, variantId: string)
	local builder = Variants[variantId]
	assert(builder, "Unknown building variant " .. tostring(variantId))
	local model = Instance.new("Model")
	model.Name = variantId
	local root = part(
		model,
		"Root",
		Vector3.new(def.Footprint[1], 0.2, def.Footprint[2]),
		CFrame.new(0, 0, 0),
		Color3.new(1, 1, 1),
		Enum.Material.SmoothPlastic,
		1
	)
	model.PrimaryPart = root
	builder(model)
	local _, size = model:GetBoundingBox()
	model:SetAttribute("VisualHeight", size.Y)
	return model
end

return BuildingModels
