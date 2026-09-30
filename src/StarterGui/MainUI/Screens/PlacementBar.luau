-- PlacementBar: bottom-center controls while placing (works on PC and mobile).
-- Shows validity: valid = neutral text, invalid = subtle red reason.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local RoadConfig = require(Config:WaitForChild("RoadConfig"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local PlacementBar = {}
PlacementBar.__index = PlacementBar

local DESIGN_W, DESIGN_H = 440, 92

local function displayName(kind, id)
	local list = kind == "Road" and RoadConfig.Types or BuildingConfig.Buildings
	for _, entry in ipairs(list) do
		if entry.Id == id then
			return entry.DisplayName
		end
	end
	return id
end

function PlacementBar.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, PlacementBar)
	self.panel = UIKit.panel({
		Name = "PlacementBar",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H + 40)
	UIKit.padding(self.panel, 10)
	self.title = UIKit.label({
		Text = "",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		Size = UDim2.new(0.5, 0, 0, 18),
		Parent = self.panel,
	})
	self.status = UIKit.label({
		Text = "",
		TextSize = T.TextSize.Small,
		TextColor3 = C.TextMuted,
		TextXAlignment = Enum.TextXAlignment.Right,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.new(0.5, 0, 0, 18),
		Parent = self.panel,
	})
	local row = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 28),
		Size = UDim2.new(1, 0, 0, 42),
		Parent = self.panel,
	})
	UIKit.list(row, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	self.styleButton = UIKit.button({
		Text = "Style A",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(84, 38),
		LayoutOrder = 1,
		Parent = row,
		OnClick = callbacks.onStyle,
	})
	UIKit.button({
		Text = "Rotate (R)",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(96, 38),
		LayoutOrder = 2,
		Parent = row,
		OnClick = callbacks.onRotate,
	})
	self.placeButton = UIKit.button({
		Text = "Place",
		Style = "primary",
		Size = UDim2.fromOffset(110, 38),
		LayoutOrder = 3,
		Parent = row,
		OnClick = callbacks.onPlace,
	})
	UIKit.button({
		Text = "Done (Q)",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(90, 38),
		LayoutOrder = 4,
		Parent = row,
		OnClick = callbacks.onDone,
	})
	return self
end

function PlacementBar:update(status)
	if not status.Active then
		return
	end
	self.title.Text = displayName(status.Kind, status.Id)
	self.styleButton.Instance.Visible = status.Kind == "Building"
	if status.Variant then
		local letter = string.match(status.Variant, "_(%w+)$") or "A"
		self.styleButton.setText("Style " .. letter)
	end
	if status.Valid then
		self.status.Text = "Ready to place"
		self.status.TextColor3 = C.TextMuted
	else
		self.status.Text = status.Reason or "Invalid placement"
		self.status.TextColor3 = C.Danger
	end
	self.placeButton.setDisabled(not status.Valid)
end

function PlacementBar:show()
	UIKit.open(self.panel)
end

function PlacementBar:hide()
	UIKit.close(self.panel)
end

return PlacementBar
