-- SlotScreen: exactly 3 save slots. Slot 1 FREE, slots 2-3 LOCKED (no monetization yet).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Countries = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Modules"):WaitForChild("Countries"))
local TechnologyConfig =
	require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("TechnologyConfig"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local SlotScreen = {}
SlotScreen.__index = SlotScreen

local DESIGN_W, DESIGN_H = 360, 350

local function techName(id)
	for _, branch in ipairs(TechnologyConfig.Branches) do
		if branch.Id == id then
			return branch.DisplayName
		end
	end
	return id or ""
end

function SlotScreen.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, SlotScreen)
	self.callbacks = callbacks
	self.panel = UIKit.panel({
		Name = "SlotScreen",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H)
	UIKit.padding(self.panel, 18)
	UIKit.list(self.panel, Enum.FillDirection.Vertical, 8)

	UIKit.label({
		Text = "WAR STATE",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Header,
		Size = UDim2.new(1, 0, 0, 26),
		LayoutOrder = 1,
		Parent = self.panel,
	})
	UIKit.label({
		Text = "Select a save slot",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		Size = UDim2.new(1, 0, 0, 16),
		LayoutOrder = 2,
		Parent = self.panel,
	})
	self.rows = UIKit.new("Frame", {
		Name = "Rows",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, 3 * 64 + 2 * 8),
		LayoutOrder = 3,
		Parent = self.panel,
	})
	UIKit.list(self.rows, Enum.FillDirection.Vertical, 8)
	self.note = UIKit.label({
		Text = "",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Size = UDim2.new(1, 0, 0, 30),
		LayoutOrder = 4,
		Parent = self.panel,
	})
	return self
end

function SlotScreen:render(profile)
	for _, child in ipairs(self.rows:GetChildren()) do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	for _, slot in ipairs(profile.slots) do
		local row = UIKit.new("Frame", {
			Name = "Slot" .. slot.Index,
			BackgroundColor3 = slot.Locked and C.Surface or C.Background,
			BorderSizePixel = 0,
			Size = UDim2.new(1, 0, 0, 64),
			LayoutOrder = slot.Index,
			Parent = self.rows,
		})
		UIKit.corner(row, T.Radius.Small)
		UIKit.stroke(row, C.Stroke)
		UIKit.padding(row, 10, 12)

		local title = "SLOT " .. slot.Index
		local subtitle
		if slot.Locked then
			subtitle = "Locked"
		elseif slot.Empty then
			subtitle = "Free · Empty"
		else
			subtitle = string.format("%s · Pop %d", techName(slot.TechnologyBranch), slot.Population or 0)
			title = slot.Name or title
		end

		local flagEntry = (not slot.Empty) and Countries.get(slot.FlagId or "") or nil
		local textX = 0
		if flagEntry then
			local flag = UIKit.flag(row, flagEntry, 26)
			flag.AnchorPoint = Vector2.new(0, 0.5)
			flag.Position = UDim2.fromScale(0, 0.5)
			textX = 44
		end
		UIKit.label({
			Text = title,
			Font = T.Fonts.Bold,
			Position = UDim2.fromOffset(textX, 2),
			Size = UDim2.new(1, -(textX + 150), 0, 20),
			TextColor3 = slot.Locked and C.TextMuted or C.Text,
			Parent = row,
		})
		UIKit.label({
			Text = subtitle,
			TextColor3 = C.TextMuted,
			TextSize = T.TextSize.Small,
			Position = UDim2.fromOffset(textX, 24),
			Size = UDim2.new(1, -(textX + 150), 0, 16),
			Parent = row,
		})

		if slot.Locked then
			local lock = UIKit.button({
				Text = "Locked",
				Size = UDim2.fromOffset(84, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.fromScale(1, 0.5),
				Parent = row,
			})
			lock.setDisabled(true)
		elseif slot.Empty then
			UIKit.button({
				Text = "Create",
				Style = "primary",
				Size = UDim2.fromOffset(84, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.fromScale(1, 0.5),
				Parent = row,
				OnClick = function()
					self.callbacks.onCreate(slot.Index)
				end,
			})
		else
			UIKit.button({
				Text = "Play",
				Style = "primary",
				Size = UDim2.fromOffset(64, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.fromScale(1, 0.5),
				Parent = row,
				OnClick = function()
					self.callbacks.onPlay(slot.Index)
				end,
			})
			local armed = false
			local delete
			delete = UIKit.button({
				Text = "Delete",
				Style = "danger",
				TextSize = T.TextSize.Small,
				Size = UDim2.fromOffset(70, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.new(1, -72, 0.5, 0),
				Parent = row,
				OnClick = function()
					if not armed then
						armed = true
						delete.setText("Confirm")
						task.delay(3, function()
							armed = false
							if delete.Instance.Parent then
								delete.setText("Delete")
							end
						end)
					else
						self.callbacks.onDelete(slot.Index)
					end
				end,
			})
		end
	end
	if profile.persistent then
		self.note.Text = "Progress is saved to your slots."
	else
		self.note.Text = "Saving is OFF this session (Studio API access disabled or DataStore unavailable)."
	end
end

function SlotScreen:show(profile)
	self:render(profile)
	UIKit.open(self.panel)
end

function SlotScreen:hide()
	UIKit.close(self.panel)
end

return SlotScreen
