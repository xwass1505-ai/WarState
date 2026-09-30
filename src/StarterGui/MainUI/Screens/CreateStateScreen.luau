-- CreateStateScreen: Country Name -> Flag (Continent -> Country) -> Technology Branch -> Create.
-- Name, Flag and Technology are independent (e.g. "Novaria" + Germany flag + USSR / Russia tech).
-- The client only collects choices; the server validates and creates the country.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Countries = require(Shared:WaitForChild("Modules"):WaitForChild("Countries"))
local TechnologyConfig = require(Shared:WaitForChild("Config"):WaitForChild("TechnologyConfig"))
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local CreateStateScreen = {}
CreateStateScreen.__index = CreateStateScreen

local DESIGN_W, DESIGN_H = 420, 470
local STEPS = { "Name", "Flag", "Technology", "Review" }

function CreateStateScreen.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, CreateStateScreen)
	self.callbacks = callbacks
	self.choice = { Name = "", FlagId = nil, Continent = nil, TechnologyBranch = nil }
	self.step = 1
	self.browseContinent = nil
	self.search = ""

	self.panel = UIKit.panel({
		Name = "CreateStateScreen",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H)
	UIKit.padding(self.panel, 18)

	self.title = UIKit.label({
		Text = "Create State",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Title,
		Size = UDim2.new(1, 0, 0, 22),
		Parent = self.panel,
	})
	self.stepLabel = UIKit.label({
		Text = "",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		Position = UDim2.fromOffset(0, 24),
		Size = UDim2.new(1, 0, 0, 16),
		Parent = self.panel,
	})
	self.dots = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, 0, 0, 6),
		Size = UDim2.fromOffset(4 * 18, 10),
		Parent = self.panel,
	})
	UIKit.list(self.dots, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Right)
	self.dotFrames = {}
	for i = 1, #STEPS do
		local dot = UIKit.new("Frame", {
			BackgroundColor3 = C.Stroke,
			BorderSizePixel = 0,
			Size = UDim2.fromOffset(10, 10),
			LayoutOrder = i,
			Parent = self.dots,
		})
		UIKit.corner(dot, 999)
		self.dotFrames[i] = dot
	end

	self.content = UIKit.new("Frame", {
		Name = "Content",
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 50),
		Size = UDim2.new(1, 0, 1, -50 - 48),
		ClipsDescendants = true,
		Parent = self.panel,
	})

	self.error = UIKit.label({
		Text = "",
		TextColor3 = C.Danger,
		TextSize = T.TextSize.Small,
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, -42),
		Size = UDim2.new(1, 0, 0, 16),
		Parent = self.panel,
	})

	self.backButton = UIKit.button({
		Text = "Back",
		Size = UDim2.fromOffset(96, 36),
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Parent = self.panel,
		OnClick = function()
			self:back()
		end,
	})
	self.nextButton = UIKit.button({
		Text = "Next",
		Style = "primary",
		Size = UDim2.fromOffset(120, 36),
		AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.fromScale(1, 1),
		Parent = self.panel,
		OnClick = function()
			self:next()
		end,
	})
	return self
end

function CreateStateScreen:setError(text: string?)
	self.error.Text = text or ""
end

function CreateStateScreen:clearContent()
	for _, child in ipairs(self.content:GetChildren()) do
		child:Destroy()
	end
end

function CreateStateScreen:canContinue(): (boolean, string?)
	if self.step == 1 then
		local name = string.match(self.choice.Name or "", "^%s*(.-)%s*$") or ""
		if #name < GameConfig.CountryName.MinLength then
			return false, "Name must be at least " .. GameConfig.CountryName.MinLength .. " characters"
		end
		if #name > GameConfig.CountryName.MaxLength then
			return false, "Name is too long"
		end
		return true, nil
	elseif self.step == 2 then
		if not self.choice.FlagId then
			return false, "Select a continent, then a country"
		end
		return true, nil
	elseif self.step == 3 then
		if not self.choice.TechnologyBranch then
			return false, "Select a technology branch"
		end
		return true, nil
	end
	return true, nil
end

function CreateStateScreen:renderName()
	UIKit.label({
		Text = "Country name",
		Font = T.Fonts.Medium,
		Size = UDim2.new(1, 0, 0, 18),
		Parent = self.content,
	})
	local box = UIKit.new("TextBox", {
		Name = "NameInput",
		BackgroundColor3 = C.Surface,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 26),
		Size = UDim2.new(1, 0, 0, 40),
		Font = T.Fonts.Medium,
		TextSize = T.TextSize.Body,
		TextColor3 = C.Text,
		PlaceholderText = "e.g. Novaria",
		PlaceholderColor3 = C.TextMuted,
		Text = self.choice.Name,
		ClearTextOnFocus = false,
		TextXAlignment = Enum.TextXAlignment.Left,
		Parent = self.content,
	})
	UIKit.corner(box, T.Radius.Small)
	local stroke = UIKit.stroke(box, C.Stroke)
	UIKit.padding(box, 0, 12)
	box.Focused:Connect(function()
		UIKit.tween(stroke, T.Motion.Fast, { Color = C.Accent })
	end)
	box.FocusLost:Connect(function()
		UIKit.tween(stroke, T.Motion.Fast, { Color = C.Stroke })
	end)
	box:GetPropertyChangedSignal("Text"):Connect(function()
		if #box.Text > GameConfig.CountryName.MaxLength then
			box.Text = string.sub(box.Text, 1, GameConfig.CountryName.MaxLength)
		end
		self.choice.Name = box.Text
		self:setError(nil)
	end)
	UIKit.label({
		Text = string.format(
			"%d-%d characters. Your name, flag and technology are independent choices.",
			GameConfig.CountryName.MinLength,
			GameConfig.CountryName.MaxLength
		),
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Position = UDim2.fromOffset(0, 74),
		Size = UDim2.new(1, 0, 0, 32),
		Parent = self.content,
	})
end

function CreateStateScreen:renderContinents()
	UIKit.label({
		Text = "Select continent",
		Font = T.Fonts.Medium,
		Size = UDim2.new(1, 0, 0, 18),
		Parent = self.content,
	})
	local grid = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 26),
		Size = UDim2.new(1, 0, 1, -26),
		Parent = self.content,
	})
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.new(0.5, -4, 0, 52)
	layout.CellPadding = UDim2.fromOffset(8, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = grid
	for i, continent in ipairs(Countries.Continents) do
		local count = #Countries.forContinent(continent)
		local b = UIKit.button({
			Text = string.upper(continent) .. "\n" .. count .. " countries",
			TextSize = T.TextSize.Small,
			LayoutOrder = i,
			Parent = grid,
			OnClick = function()
				self.browseContinent = continent
				self.search = ""
				self:render()
			end,
		})
		if self.choice.Continent == continent then
			b.setSelected(true)
		end
	end
end

function CreateStateScreen:renderCountries()
	local continent = self.browseContinent
	UIKit.button({
		Text = "< Continents",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(104, 28),
		Style = "ghost",
		Parent = self.content,
		OnClick = function()
			self.browseContinent = nil
			self:render()
		end,
	})
	UIKit.label({
		Text = string.upper(continent),
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		TextXAlignment = Enum.TextXAlignment.Right,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.new(0.5, 0, 0, 28),
		Parent = self.content,
	})
	local search = UIKit.new("TextBox", {
		Name = "Search",
		BackgroundColor3 = C.Surface,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 34),
		Size = UDim2.new(1, 0, 0, 30),
		Font = T.Fonts.Regular,
		TextSize = T.TextSize.Small,
		TextColor3 = C.Text,
		PlaceholderText = "Search in " .. continent .. " (optional)",
		PlaceholderColor3 = C.TextMuted,
		Text = self.search,
		ClearTextOnFocus = false,
		TextXAlignment = Enum.TextXAlignment.Left,
		Parent = self.content,
	})
	UIKit.corner(search, T.Radius.Small)
	UIKit.stroke(search, C.Stroke)
	UIKit.padding(search, 0, 10)

	local list = UIKit.vScroll({
		Name = "CountryList",
		Position = UDim2.fromOffset(0, 70),
		Size = UDim2.new(1, 0, 1, -70),
		Parent = self.content,
	})
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.new(0.5, -6, 0, 36)
	layout.CellPadding = UDim2.fromOffset(6, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list
	UIKit.padding(list, 2, 2)

	local buttons = {}
	local function populate()
		for _, b in ipairs(buttons) do
			b.Instance:Destroy()
		end
		buttons = {}
		for i, entry in ipairs(Countries.search(self.search, continent)) do
			local b
			b = UIKit.button({
				Text = "",
				LayoutOrder = i,
				Parent = list,
				OnClick = function()
					self.choice.FlagId = entry.Id
					self.choice.Continent = entry.Continent
					self:setError(nil)
					for _, other in ipairs(buttons) do
						other.setSelected(other == b)
					end
				end,
			})
			local flag = UIKit.flag(b.Instance, entry, 18)
			flag.AnchorPoint = Vector2.new(0, 0.5)
			flag.Position = UDim2.new(0, 8, 0.5, 0)
			UIKit.label({
				Text = entry.DisplayNameEN,
				TextSize = T.TextSize.Small,
				Position = UDim2.fromOffset(40, 0),
				Size = UDim2.new(1, -46, 1, 0),
				Parent = b.Instance,
			})
			if self.choice.FlagId == entry.Id then
				b.setSelected(true)
			end
			table.insert(buttons, b)
		end
	end
	populate()
	search:GetPropertyChangedSignal("Text"):Connect(function()
		self.search = search.Text
		populate()
	end)
end

function CreateStateScreen:renderTechnology()
	UIKit.label({
		Text = "Technology branch",
		Font = T.Fonts.Medium,
		Size = UDim2.new(1, 0, 0, 18),
		Parent = self.content,
	})
	local holder = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 26),
		Size = UDim2.new(1, 0, 1, -26),
		Parent = self.content,
	})
	UIKit.list(holder, Enum.FillDirection.Vertical, 8)
	local buttons = {}
	for i, branch in ipairs(TechnologyConfig.Branches) do
		local b
		b = UIKit.button({
			Text = "",
			Size = UDim2.new(1, 0, 0, 58),
			LayoutOrder = i,
			Parent = holder,
			OnClick = function()
				self.choice.TechnologyBranch = branch.Id
				self:setError(nil)
				for _, other in ipairs(buttons) do
					other.setSelected(other == b)
				end
			end,
		})
		UIKit.label({
			Text = branch.DisplayName,
			Font = T.Fonts.Bold,
			Position = UDim2.fromOffset(14, 8),
			Size = UDim2.new(1, -28, 0, 20),
			Parent = b.Instance,
		})
		UIKit.label({
			Text = branch.Description,
			TextColor3 = C.TextMuted,
			TextSize = T.TextSize.Small,
			Position = UDim2.fromOffset(14, 30),
			Size = UDim2.new(1, -28, 0, 18),
			Parent = b.Instance,
		})
		if self.choice.TechnologyBranch == branch.Id then
			b.setSelected(true)
		end
		table.insert(buttons, b)
	end
end

function CreateStateScreen:renderReview()
	local entry = Countries.get(self.choice.FlagId or "")
	local techName = self.choice.TechnologyBranch
	for _, branch in ipairs(TechnologyConfig.Branches) do
		if branch.Id == self.choice.TechnologyBranch then
			techName = branch.DisplayName
		end
	end
	local card = UIKit.new("Frame", {
		BackgroundColor3 = C.Surface,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, 150),
		Parent = self.content,
	})
	UIKit.corner(card, T.Radius.Small)
	UIKit.stroke(card, C.Stroke)
	UIKit.padding(card, 14)
	local flag = UIKit.flag(card, entry, 34)
	flag.Position = UDim2.fromOffset(0, 0)
	UIKit.label({
		Text = self.choice.Name,
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Title,
		Position = UDim2.fromOffset(60, 0),
		Size = UDim2.new(1, -60, 0, 22),
		Parent = card,
	})
	UIKit.label({
		Text = "Flag: " .. (entry and entry.DisplayNameEN or "-") .. " · " .. (self.choice.Continent or ""),
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		Position = UDim2.fromOffset(60, 24),
		Size = UDim2.new(1, -60, 0, 16),
		Parent = card,
	})
	UIKit.label({
		Text = "Technology: " .. tostring(techName),
		TextColor3 = C.Text,
		TextSize = T.TextSize.Small,
		Position = UDim2.fromOffset(0, 56),
		Size = UDim2.new(1, 0, 0, 18),
		Parent = card,
	})
	UIKit.label({
		Text = "Your state starts empty: no money, citizens, houses or roads. Build it from zero.",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Position = UDim2.fromOffset(0, 80),
		Size = UDim2.new(1, 0, 0, 36),
		Parent = card,
	})
end

function CreateStateScreen:render()
	self:clearContent()
	self.stepLabel.Text = string.format("Step %d of %d · %s", self.step, #STEPS, STEPS[self.step])
	for i, dot in ipairs(self.dotFrames) do
		UIKit.tween(dot, T.Motion.Normal, { BackgroundColor3 = (i <= self.step) and C.Accent or C.Stroke })
	end
	self.backButton.setText(self.step == 1 and "Cancel" or "Back")
	self.nextButton.setText(self.step == #STEPS and "Create State" or "Next")
	if self.step == 1 then
		self:renderName()
	elseif self.step == 2 then
		if self.browseContinent then
			self:renderCountries()
		else
			self:renderContinents()
		end
	elseif self.step == 3 then
		self:renderTechnology()
	else
		self:renderReview()
	end
end

function CreateStateScreen:next()
	if self.submitting then
		return
	end
	local ok, reason = self:canContinue()
	if not ok then
		self:setError(reason)
		return
	end
	self:setError(nil)
	if self.step < #STEPS then
		self.step += 1
		if self.step == 2 then
			self.browseContinent = self.choice.Continent
		end
		self:render()
		return
	end
	self.submitting = true
	self.nextButton.setText("Creating...")
	local payload = {
		Name = string.match(self.choice.Name, "^%s*(.-)%s*$"),
		FlagId = self.choice.FlagId,
		Continent = self.choice.Continent,
		TechnologyBranch = self.choice.TechnologyBranch,
	}
	task.spawn(function()
		local result = self.callbacks.onSubmit(self.slotIndex, payload)
		self.submitting = false
		if result and result.ok then
			self:hide()
		else
			self.nextButton.setText("Create State")
			self:setError(result and result.error or "Could not create state")
		end
	end)
end

function CreateStateScreen:back()
	if self.submitting then
		return
	end
	self:setError(nil)
	if self.step == 2 and self.browseContinent then
		self.browseContinent = nil
		self:render()
		return
	end
	if self.step == 1 then
		self:hide()
		self.callbacks.onCancel()
		return
	end
	self.step -= 1
	self:render()
end

function CreateStateScreen:show(slotIndex: number)
	self.slotIndex = slotIndex
	self.choice = { Name = "", FlagId = nil, Continent = nil, TechnologyBranch = nil }
	self.step = 1
	self.browseContinent = nil
	self.search = ""
	self.submitting = false
	self:setError(nil)
	self.title.Text = "Create State · Slot " .. slotIndex
	self:render()
	UIKit.open(self.panel)
end

function CreateStateScreen:hide()
	UIKit.close(self.panel)
end

return CreateStateScreen
