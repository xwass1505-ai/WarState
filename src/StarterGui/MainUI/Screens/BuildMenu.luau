-- BuildMenu: compact bottom-center menu. HAMMER -> BUILD -> CATEGORY -> BUILDING.
-- Categories scroll horizontally (touch drag on mobile, mouse wheel / drag on PC).
-- Roads is always the FIRST category so it is always reachable.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local BuildMenuConfig = require(Config:WaitForChild("BuildMenuConfig"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local RoadConfig = require(Config:WaitForChild("RoadConfig"))
local BuildingModels = require(Shared:WaitForChild("Modules"):WaitForChild("BuildingModels"))
local RoadModels = require(Shared:WaitForChild("Modules"):WaitForChild("RoadModels"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local BuildMenu = {}
BuildMenu.__index = BuildMenu

local DESIGN_W, DESIGN_H = 560, 214

local function itemsForCategory(categoryId: string)
	local items = {}
	if categoryId == "Roads" then
		for _, roadType in ipairs(RoadConfig.Types) do
			if roadType.Active then
				table.insert(items, {
					Kind = "Road",
					Id = roadType.Id,
					Name = roadType.DisplayName,
					Meta = "Instant",
				})
			end
		end
	else
		for _, def in ipairs(BuildingConfig.Buildings) do
			if def.Category == categoryId and def.Active then
				table.insert(items, {
					Kind = "Building",
					Id = def.Id,
					Name = def.DisplayName,
					Meta = string.format("+%d housing · %ds", def.HousingCapacity or 0, def.BuildTimeSeconds),
					Def = def,
				})
			end
		end
	end
	return items
end

local function viewport(parent, item)
	local frame = UIKit.new("ViewportFrame", {
		BackgroundColor3 = C.SurfaceAlt,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, 70),
		Ambient = Color3.fromRGB(200, 205, 215),
		LightColor = Color3.fromRGB(255, 255, 255),
		LightDirection = Vector3.new(-1, -2, -1),
		Parent = parent,
	})
	UIKit.corner(frame, 8)
	local model
	if item.Kind == "Road" then
		model = RoadModels.build(item.Id)
	else
		model = BuildingModels.build(item.Def, item.Def.Variants[1])
	end
	model.Parent = frame
	local cf, size = model:GetBoundingBox()
	local radius = size.Magnitude / 2
	local camera = Instance.new("Camera")
	camera.FieldOfView = 30
	local direction = Vector3.new(1, 0.9, 1.2).Unit
	camera.CFrame = CFrame.lookAt(cf.Position + direction * radius * 3.4, cf.Position)
	camera.Parent = frame
	frame.CurrentCamera = camera
	return frame
end

function BuildMenu.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, BuildMenu)
	self.callbacks = callbacks
	self.categoryButtons = {}
	self.currentCategory = BuildMenuConfig.Categories[1].Id

	self.panel = UIKit.panel({
		Name = "BuildMenu",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H + 40)
	UIKit.padding(self.panel, 10)

	UIKit.label({
		Text = "BUILD",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		TextColor3 = C.AccentDark,
		Size = UDim2.fromOffset(60, 28),
		Parent = self.panel,
	})
	UIKit.button({
		Text = "Close",
		TextSize = T.TextSize.Small,
		Style = "ghost",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.fromOffset(60, 28),
		Parent = self.panel,
		OnClick = function()
			self:hide()
			self.callbacks.onClose()
		end,
	})

	self.categories = UIKit.hScroll({
		Name = "Categories",
		Position = UDim2.fromOffset(64, 0),
		Size = UDim2.new(1, -64 - 66, 0, 32),
		Spacing = 6,
		Parent = self.panel,
	})
	for i, category in ipairs(BuildMenuConfig.Categories) do
		local b = UIKit.button({
			Text = category.DisplayName,
			TextSize = T.TextSize.Small,
			Size = UDim2.fromOffset(96, 28),
			Radius = 999,
			LayoutOrder = i,
			Parent = self.categories,
			OnClick = function()
				self:selectCategory(category.Id)
			end,
		})
		self.categoryButtons[category.Id] = b
	end

	self.items = UIKit.hScroll({
		Name = "Items",
		Position = UDim2.fromOffset(0, 40),
		Size = UDim2.new(1, 0, 1, -40),
		Spacing = 8,
		Parent = self.panel,
	})
	return self
end

function BuildMenu:selectCategory(categoryId: string)
	self.currentCategory = categoryId
	for id, b in pairs(self.categoryButtons) do
		b.setSelected(id == categoryId)
	end
	for _, child in ipairs(self.items:GetChildren()) do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	self.items.CanvasPosition = Vector2.new(0, 0)
	local items = itemsForCategory(categoryId)
	if #items == 0 then
		UIKit.label({
			Text = "Planned for a future update",
			TextColor3 = C.TextMuted,
			TextSize = T.TextSize.Small,
			TextXAlignment = Enum.TextXAlignment.Center,
			Size = UDim2.fromOffset(DESIGN_W - 20, 120),
			Parent = self.items,
		})
		return
	end
	for i, item in ipairs(items) do
		local card = UIKit.button({
			Name = item.Id,
			Text = "",
			Size = UDim2.fromOffset(118, 124),
			LayoutOrder = i,
			Parent = self.items,
			OnClick = function()
				self:hide()
				self.callbacks.onSelect(item.Kind, item.Id)
			end,
		})
		UIKit.padding(card.Instance, 6)
		local vp = viewport(card.Instance, item)
		vp.Active = false
		UIKit.label({
			Text = item.Name,
			Font = T.Fonts.Bold,
			TextSize = T.TextSize.Small,
			Position = UDim2.fromOffset(0, 76),
			Size = UDim2.new(1, 0, 0, 18),
			Parent = card.Instance,
		})
		UIKit.label({
			Text = item.Meta,
			TextColor3 = C.TextMuted,
			TextSize = 11,
			Position = UDim2.fromOffset(0, 96),
			Size = UDim2.new(1, 0, 0, 16),
			Parent = card.Instance,
		})
	end
end

function BuildMenu:show(categoryId: string?)
	self:selectCategory(categoryId or self.currentCategory)
	UIKit.open(self.panel)
end

function BuildMenu:hide()
	UIKit.close(self.panel)
end

function BuildMenu:isOpen(): boolean
	return self.panel.Visible
end

return BuildMenu
