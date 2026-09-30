-- HUD: TOP CENTER menu + country + population indicator; BOTTOM CENTER hammer (Build).
-- Compact pills only. Respects the Roblox Core UI safe inset (ScreenGui.ScreenInsets).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Countries = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Modules"):WaitForChild("Countries"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local HUD = {}
HUD.__index = HUD

function HUD.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, HUD)
	self.callbacks = callbacks

	-- TOP CENTER bar
	self.top = UIKit.new("Frame", {
		Name = "TopCenter",
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 8),
		Size = UDim2.fromOffset(0, 38),
		AutomaticSize = Enum.AutomaticSize.X,
		Visible = false,
		Parent = root,
	})
	UIKit.corner(self.top, 999)
	UIKit.stroke(self.top, C.Stroke)
	UIKit.padding(self.top, 4, 6)
	UIKit.list(self.top, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)

	self.menuButton = UIKit.button({
		Name = "Menu",
		Text = "Menu",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(58, 30),
		Radius = 999,
		LayoutOrder = 1,
		Parent = self.top,
		OnClick = function()
			self:toggleMenu()
		end,
	})

	self.flagHolder = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Size = UDim2.fromOffset(25, 18),
		LayoutOrder = 2,
		Parent = self.top,
	})
	self.nameLabel = UIKit.label({
		Text = "",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		LayoutOrder = 3,
		Parent = self.top,
	})
	UIKit.new("Frame", {
		BackgroundColor3 = C.Stroke,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(1, 18),
		LayoutOrder = 4,
		Parent = self.top,
	})
	self.popLabel = UIKit.label({
		Name = "Population",
		Text = "Population 0 / 0",
		TextSize = T.TextSize.Small,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		LayoutOrder = 5,
		Parent = self.top,
	})
	self.saveChip = UIKit.label({
		Text = "Saving off",
		TextColor3 = C.Danger,
		TextSize = 11,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		LayoutOrder = 6,
		Visible = false,
		Parent = self.top,
	})

	-- Menu popover (under the top bar)
	self.menu = UIKit.panel({
		Name = "MenuPopover",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 52),
		Size = UDim2.fromOffset(180, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Visible = false,
		Parent = root,
	})
	UIKit.padding(self.menu, 8)
	UIKit.list(self.menu, Enum.FillDirection.Vertical, 6)
	UIKit.button({
		Text = "Save now",
		Size = UDim2.new(1, 0, 0, 32),
		LayoutOrder = 1,
		Parent = self.menu,
		OnClick = function()
			self:closeMenu()
			self.callbacks.onSave()
		end,
	})
	UIKit.button({
		Text = "Change slot",
		Size = UDim2.new(1, 0, 0, 32),
		LayoutOrder = 2,
		Parent = self.menu,
		OnClick = function()
			self:closeMenu()
			self.callbacks.onChangeSlot()
		end,
	})
	self.statsLabel = UIKit.label({
		Text = "",
		TextColor3 = C.TextMuted,
		TextSize = 11,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Size = UDim2.new(1, 0, 0, 44),
		LayoutOrder = 3,
		Parent = self.menu,
	})

	-- BOTTOM CENTER hammer
	self.hammer = UIKit.new("TextButton", {
		Name = "Hammer",
		AutoButtonColor = false,
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14),
		Size = UDim2.fromOffset(60, 60),
		Text = "",
		Visible = false,
		Parent = root,
	})
	UIKit.corner(self.hammer, 999)
	local hammerStroke = UIKit.stroke(self.hammer, C.Stroke, 1.5)
	local hammerScale = Instance.new("UIScale")
	hammerScale.Parent = self.hammer
	UIKit.label({
		Text = "🔨",
		TextSize = 22,
		TextXAlignment = Enum.TextXAlignment.Center,
		Position = UDim2.fromOffset(0, 8),
		Size = UDim2.new(1, 0, 0, 26),
		Parent = self.hammer,
	})
	UIKit.label({
		Text = "BUILD",
		Font = T.Fonts.Bold,
		TextSize = 10,
		TextColor3 = C.AccentDark,
		TextXAlignment = Enum.TextXAlignment.Center,
		Position = UDim2.fromOffset(0, 36),
		Size = UDim2.new(1, 0, 0, 14),
		Parent = self.hammer,
	})
	self.hammer.MouseEnter:Connect(function()
		UIKit.tween(self.hammer, T.Motion.Fast, { BackgroundColor3 = C.Surface })
		UIKit.tween(hammerStroke, T.Motion.Fast, { Color = C.Accent })
	end)
	self.hammer.MouseLeave:Connect(function()
		UIKit.tween(self.hammer, T.Motion.Fast, { BackgroundColor3 = C.Background })
		UIKit.tween(hammerStroke, T.Motion.Fast, { Color = C.Stroke })
		UIKit.tween(hammerScale, T.Motion.Fast, { Scale = 1 })
	end)
	self.hammer.MouseButton1Down:Connect(function()
		UIKit.tween(hammerScale, T.Motion.Fast, { Scale = 0.94 })
	end)
	self.hammer.MouseButton1Up:Connect(function()
		UIKit.tween(hammerScale, T.Motion.Fast, { Scale = 1 })
	end)
	self.hammer.Activated:Connect(function()
		self:toggleTools()
	end)

	-- Hammer tool popover: HAMMER -> BUILD
	self.tools = UIKit.panel({
		Name = "HammerTools",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -84),
		Size = UDim2.fromOffset(0, 48),
		AutomaticSize = Enum.AutomaticSize.X,
		Visible = false,
		Parent = root,
	})
	UIKit.padding(self.tools, 6)
	UIKit.list(self.tools, Enum.FillDirection.Horizontal, 6, nil, Enum.VerticalAlignment.Center)
	UIKit.button({
		Text = "Build",
		Style = "primary",
		Size = UDim2.fromOffset(92, 36),
		LayoutOrder = 1,
		Parent = self.tools,
		OnClick = function()
			self:closeTools()
			self.callbacks.onOpenBuild()
		end,
	})
	local demolish = UIKit.button({
		Text = "Demolish · soon",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(120, 36),
		LayoutOrder = 2,
		Parent = self.tools,
	})
	demolish.setDisabled(true)
	return self
end

function HUD:toggleTools()
	if self.tools.Visible then
		self:closeTools()
	else
		self.callbacks.onHammer()
		UIKit.open(self.tools)
	end
end

function HUD:closeTools()
	UIKit.close(self.tools)
end

function HUD:toggleMenu()
	if self.menu.Visible then
		self:closeMenu()
	else
		UIKit.open(self.menu, -6)
	end
end

function HUD:closeMenu()
	UIKit.close(self.menu, -6)
end

function HUD:setHammerVisible(visible: boolean)
	self.hammer.Visible = visible
	if not visible then
		self.tools.Visible = false
	end
end

function HUD:show()
	UIKit.open(self.top, -8)
	self.hammer.Visible = true
end

function HUD:hide()
	self.top.Visible = false
	self.menu.Visible = false
	self.tools.Visible = false
	self.hammer.Visible = false
end

function HUD:update(state)
	if not state or not state.Active then
		return
	end
	if self.lastFlag ~= state.FlagId then
		self.lastFlag = state.FlagId
		for _, child in ipairs(self.flagHolder:GetChildren()) do
			child:Destroy()
		end
		local flag = UIKit.flag(self.flagHolder, Countries.get(state.FlagId or ""), 18)
		flag.Size = UDim2.fromScale(1, 1)
	end
	self.nameLabel.Text = state.Name or ""
	local previous = self.lastPopulation
	self.popLabel.Text = string.format("Population %d / %d", state.Population or 0, state.HousingCapacity or 0)
	if previous ~= nil and state.Population ~= previous then
		self.popLabel.TextColor3 = C.AccentDark
		UIKit.tween(self.popLabel, T.Motion.Slow, { TextColor3 = C.Text })
	end
	self.lastPopulation = state.Population
	self.saveChip.Visible = state.Persistent == false
	self.statsLabel.Text = string.format(
		"Buildings %d (%d building) · Roads %d · Workers %d",
		state.BuildingCount or 0,
		state.UnderConstruction or 0,
		state.RoadCount or 0,
		state.Workers or 0
	)
end

return HUD
