-- PlacementController: client-side build preview only.
-- Shows a snapped preview, validates it locally with the SAME PlacementRules the server uses,
-- and sends a placement REQUEST. The server re-validates and decides.
-- PC: mouse to aim, Left click place, R rotate, Q/Esc cancel.
-- Mobile: tap the ground to aim, then use the on-screen Place / Rotate / Cancel buttons.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local Modules = Shared:WaitForChild("Modules")
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local BuildingModels = require(Modules:WaitForChild("BuildingModels"))
local RoadModels = require(Modules:WaitForChild("RoadModels"))
local Plots = require(Modules:WaitForChild("Plots"))

local player = Players.LocalPlayer
local Remotes = ReplicatedStorage:WaitForChild("Remotes")

local PlacementController = {}

local defsById = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	defsById[def.Id] = def
end

local active = nil -- { kind, id, variantIndex, rotation, model, highlight, valid, reason, info }
local connections = {}
local listeners = {}
local aimScreen = nil -- Vector2 (touch aim point) or nil for mouse
local requesting = false

local INVALID_COLOR = Color3.fromRGB(
	PlacementConfig.PreviewInvalidColor[1],
	PlacementConfig.PreviewInvalidColor[2],
	PlacementConfig.PreviewInvalidColor[3]
)

local function emit()
	local status = PlacementController.getStatus()
	for _, fn in ipairs(listeners) do
		task.spawn(fn, status)
	end
end

function PlacementController.onStatus(fn)
	table.insert(listeners, fn)
end

function PlacementController.getStatus()
	if not active then
		return { Active = false }
	end
	local variantName = nil
	if active.kind == "Building" then
		variantName = defsById[active.id].Variants[active.variantIndex]
	end
	return {
		Active = true,
		Kind = active.kind,
		Id = active.id,
		Variant = variantName,
		Valid = active.valid,
		Reason = active.reason,
		Rotation = active.rotation,
		HasAim = active.info ~= nil,
	}
end

local function plotBounds()
	local index = player:GetAttribute(Constants.Attributes.PlotIndex)
	if not index then
		return nil
	end
	return Plots.getBounds(index)
end

-- Build validation context from replicated world models (server-created, attribute-tagged).
local function buildContext(bounds)
	local ctx = { plot = bounds, buildingRects = {}, roadCells = {} }
	local folderName = "Plot_" .. bounds.index
	local buildings = Workspace:FindFirstChild("Buildings")
	local roads = Workspace:FindFirstChild("Roads")
	local bFolder = buildings and buildings:FindFirstChild(folderName)
	local rFolder = roads and roads:FindFirstChild(folderName)
	local function rectOf(model)
		local minX = model:GetAttribute("RectMinX")
		if minX == nil then
			return nil
		end
		return {
			minX = minX,
			maxX = model:GetAttribute("RectMaxX"),
			minZ = model:GetAttribute("RectMinZ"),
			maxZ = model:GetAttribute("RectMaxZ"),
		}
	end
	if bFolder then
		for _, model in ipairs(bFolder:GetChildren()) do
			local rect = rectOf(model)
			if rect then
				table.insert(ctx.buildingRects, rect)
			end
		end
	end
	if rFolder then
		for _, model in ipairs(rFolder:GetChildren()) do
			local rect = rectOf(model)
			local ix, iz = model:GetAttribute("Ix"), model:GetAttribute("Iz")
			if rect and ix ~= nil and iz ~= nil then
				ctx.roadCells[GridMath.cellKey(ix, iz)] = rect
			end
		end
	end
	return ctx
end

local function setPreviewLook(model, valid: boolean)
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			local base = d:GetAttribute("BaseTransparency") or 0
			d.Transparency = math.max(base, PlacementConfig.PreviewTransparency)
		end
	end
	if active and active.highlight then
		active.highlight.Enabled = not valid
	end
end

local function destroyPreview()
	if active and active.model then
		active.model:Destroy()
		active.model = nil
	end
	if active and active.highlight then
		active.highlight:Destroy()
		active.highlight = nil
	end
end

local function createPreview()
	destroyPreview()
	local model
	if active.kind == "Road" then
		model = RoadModels.build(active.id)
	else
		local def = defsById[active.id]
		model = BuildingModels.build(def, def.Variants[active.variantIndex])
	end
	model.Name = "PlacementPreview"
	local highlight = Instance.new("Highlight")
	highlight.Name = "InvalidHighlight"
	highlight.FillColor = INVALID_COLOR
	highlight.OutlineColor = INVALID_COLOR
	highlight.FillTransparency = 0.55
	highlight.OutlineTransparency = 0.4
	highlight.DepthMode = Enum.HighlightDepthMode.Occluded
	highlight.Enabled = false
	highlight.Adornee = model
	highlight.Parent = model
	active.model = model
	active.highlight = highlight
	model.Parent = Workspace.CurrentCamera
	setPreviewLook(model, true)
end

local function raycastGround(screenPoint: Vector2)
	local camera = Workspace.CurrentCamera
	local map = Workspace:FindFirstChild("Map")
	if not camera or not map then
		return nil
	end
	local ray = camera:ViewportPointToRay(screenPoint.X, screenPoint.Y)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { map }
	local result = Workspace:Raycast(ray.Origin, ray.Direction * PlacementConfig.MaxPlacementRayDistance, params)
	return result and result.Position or nil
end

local function currentScreenPoint(): Vector2?
	if aimScreen then
		return aimScreen
	end
	if UserInputService.MouseEnabled then
		-- GetMouseLocation is in viewport space, matching ViewportPointToRay.
		return UserInputService:GetMouseLocation()
	end
	return nil
end

local function update()
	if not active or not active.model then
		return
	end
	local bounds = plotBounds()
	local screenPoint = currentScreenPoint()
	local hit = (bounds and screenPoint) and raycastGround(screenPoint) or nil
	if not hit then
		active.info = nil
		active.valid = false
		active.reason = "Aim at your territory"
		active.model.Parent = nil
		return
	end
	active.model.Parent = Workspace.CurrentCamera
	local ctx = buildContext(bounds)
	local ok, reason, info
	if active.kind == "Road" then
		ok, reason, info = PlacementRules.validateRoad(hit.X, hit.Z, ctx)
	else
		ok, reason, info = PlacementRules.validateBuilding(defsById[active.id], hit.X, hit.Z, active.rotation, ctx)
	end
	active.hitX, active.hitZ = hit.X, hit.Z
	active.info = info
	local changed = active.valid ~= ok or active.reason ~= reason
	active.valid = ok
	active.reason = reason
	if info then
		active.model:PivotTo(
			CFrame.new(info.centerX, bounds.surfaceY + 0.02, info.centerZ)
				* CFrame.Angles(0, GridMath.yawForRotation(active.rotation), 0)
		)
	end
	if changed then
		setPreviewLook(active.model, ok)
		emit()
	end
end

function PlacementController.isActive(): boolean
	return active ~= nil
end

function PlacementController.start(kind: string, id: string)
	PlacementController.cancel()
	active = { kind = kind, id = id, variantIndex = 1, rotation = 0, valid = false, reason = "Aim at your territory" }
	aimScreen = nil
	createPreview()
	table.insert(connections, RunService.RenderStepped:Connect(update))
	table.insert(connections, UserInputService.InputBegan:Connect(function(input, processed)
		if processed then
			return
		end
		if input.KeyCode == Enum.KeyCode.R then
			PlacementController.rotate()
		elseif input.KeyCode == Enum.KeyCode.Q or input.KeyCode == Enum.KeyCode.Escape then
			PlacementController.cancel()
		elseif input.UserInputType == Enum.UserInputType.MouseButton1 then
			aimScreen = nil
			PlacementController.confirm()
		end
	end))
	table.insert(connections, UserInputService.TouchTapInWorld:Connect(function(position, processed)
		if not processed then
			aimScreen = position
		end
	end))
	emit()
end

function PlacementController.rotate()
	if not active then
		return
	end
	active.rotation = (active.rotation + 1) % 4
	active.reason = nil
	emit()
end

function PlacementController.cycleVariant()
	if not active or active.kind ~= "Building" then
		return
	end
	local def = defsById[active.id]
	active.variantIndex = (active.variantIndex % #def.Variants) + 1
	createPreview()
	active.reason = nil
	emit()
end

function PlacementController.cancel()
	for _, c in ipairs(connections) do
		c:Disconnect()
	end
	connections = {}
	destroyPreview()
	local wasActive = active ~= nil
	active = nil
	aimScreen = nil
	if wasActive then
		emit()
	end
end

-- Returns via callback(ok, message). The server is the authority.
function PlacementController.confirm(callback)
	if not active or requesting then
		return
	end
	if not active.info or not active.valid then
		if callback then
			callback(false, active.reason or "Invalid placement")
		end
		emit()
		return
	end
	requesting = true
	local request
	local remote
	if active.kind == "Road" then
		remote = Remotes:WaitForChild(Constants.Remotes.PlaceRoad)
		request = { Type = active.id, X = active.info.centerX, Z = active.info.centerZ, Rotation = active.rotation }
	else
		remote = Remotes:WaitForChild(Constants.Remotes.PlaceBuilding)
		local def = defsById[active.id]
		request = {
			Type = active.id,
			Variant = def.Variants[active.variantIndex],
			X = active.info.centerX,
			Z = active.info.centerZ,
			Rotation = active.rotation,
		}
	end
	task.spawn(function()
		local ok, result = pcall(function()
			return remote:InvokeServer(request)
		end)
		requesting = false
		local success = ok and type(result) == "table" and result.ok == true
		local message = success and "Placed" or ((ok and type(result) == "table" and result.error) or "Request failed")
		for _, fn in ipairs(PlacementController.resultListeners) do
			task.spawn(fn, success, message)
		end
		if callback then
			callback(success, message)
		end
	end)
end

PlacementController.resultListeners = {}
function PlacementController.onResult(fn)
	table.insert(PlacementController.resultListeners, fn)
end

return PlacementController
