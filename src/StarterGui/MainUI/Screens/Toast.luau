-- Toast: small, short-lived notification under the top-center HUD.

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local C = UIKit.Theme.Colors

local Toast = {}
Toast.__index = Toast

function Toast.new(root: ScreenGui)
	local self = setmetatable({}, Toast)
	self.container = UIKit.new("Frame", {
		Name = "Toasts",
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 58),
		Size = UDim2.fromOffset(320, 120),
		Parent = root,
	})
	UIKit.list(self.container, Enum.FillDirection.Vertical, 6, Enum.HorizontalAlignment.Center)
	return self
end

function Toast:show(text: string, kind: string?)
	local color = C.Text
	if kind == "error" then
		color = C.Danger
	elseif kind == "success" then
		color = C.AccentDark
	end
	local item = UIKit.new("Frame", {
		Name = "Toast",
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		Parent = self.container,
	})
	UIKit.corner(item, 999)
	UIKit.stroke(item, C.Stroke)
	UIKit.padding(item, 0, 14)
	local label = UIKit.label({
		Text = text,
		TextColor3 = color,
		TextSize = UIKit.Theme.TextSize.Small,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		TextXAlignment = Enum.TextXAlignment.Center,
		Parent = item,
	})
	label.TextTransparency = 1
	item.BackgroundTransparency = 1
	UIKit.tween(label, 0.15, { TextTransparency = 0 })
	UIKit.tween(item, 0.15, { BackgroundTransparency = 0 })
	task.delay(2.4, function()
		if item.Parent then
			UIKit.tween(label, 0.2, { TextTransparency = 1 })
			local t = UIKit.tween(item, 0.2, { BackgroundTransparency = 1 })
			t.Completed:Connect(function()
				item:Destroy()
			end)
		end
	end)
	local items = {}
	for _, child in ipairs(self.container:GetChildren()) do
		if child:IsA("Frame") then
			table.insert(items, child)
		end
	end
	if #items > 3 then
		items[1]:Destroy()
	end
end

return Toast
