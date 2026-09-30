-- UIKit: tiny UI toolkit (instance factory, theme, subtle TweenService motion).
-- Motion rules: short, subtle, no glow, no constant movement.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Theme = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("ThemeConfig"))

local UIKit = {}
UIKit.Theme = Theme
local C = Theme.Colors

function UIKit.new(className: string, props, children)
	local inst = Instance.new(className)
	local parent = nil
	for key, value in pairs(props or {}) do
		if key == "Parent" then
			parent = value
		else
			inst[key] = value
		end
	end
	for _, child in ipairs(children or {}) do
		child.Parent = inst
	end
	if parent then
		inst.Parent = parent
	end
	return inst
end

function UIKit.tween(inst: Instance, duration: number, props, style, direction)
	local info = TweenInfo.new(duration, style or Theme.Motion.Style, direction or Theme.Motion.Direction)
	local tween = TweenService:Create(inst, info, props)
	tween:Play()
	return tween
end

function UIKit.corner(parent: Instance, radius: number?)
	local c = Instance.new("UICorner")
	if radius == nil or radius >= 999 then
		c.CornerRadius = UDim.new(1, 0)
	else
		c.CornerRadius = UDim.new(0, radius)
	end
	c.Parent = parent
	return c
end

function UIKit.stroke(parent: Instance, color: Color3?, thickness: number?, transparency: number?)
	local s = Instance.new("UIStroke")
	s.Color = color or C.Stroke
	s.Thickness = thickness or 1
	s.Transparency = transparency or 0
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = parent
	return s
end

function UIKit.padding(parent: Instance, all: number, horizontal: number?)
	local p = Instance.new("UIPadding")
	local h = horizontal or all
	p.PaddingTop = UDim.new(0, all)
	p.PaddingBottom = UDim.new(0, all)
	p.PaddingLeft = UDim.new(0, h)
	p.PaddingRight = UDim.new(0, h)
	p.Parent = parent
	return p
end

function UIKit.list(parent: Instance, direction, spacing: number, hAlign, vAlign)
	local l = Instance.new("UIListLayout")
	l.FillDirection = direction or Enum.FillDirection.Vertical
	l.Padding = UDim.new(0, spacing or 6)
	l.SortOrder = Enum.SortOrder.LayoutOrder
	l.HorizontalAlignment = hAlign or Enum.HorizontalAlignment.Left
	l.VerticalAlignment = vAlign or Enum.VerticalAlignment.Top
	l.Parent = parent
	return l
end

function UIKit.label(props)
	local defaults = {
		BackgroundTransparency = 1,
		Font = Theme.Fonts.Medium,
		TextSize = Theme.TextSize.Body,
		TextColor3 = C.Text,
		TextXAlignment = Enum.TextXAlignment.Left,
		TextYAlignment = Enum.TextYAlignment.Center,
		Size = UDim2.new(1, 0, 0, 20),
		Text = "",
		TextTruncate = Enum.TextTruncate.AtEnd,
	}
	for k, v in pairs(props or {}) do
		defaults[k] = v
	end
	return UIKit.new("TextLabel", defaults)
end

-- Compact panel with white background, soft stroke and rounded corners.
function UIKit.panel(props)
	local defaults = {
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(320, 200),
	}
	for k, v in pairs(props or {}) do
		defaults[k] = v
	end
	local frame = UIKit.new("Frame", defaults)
	UIKit.corner(frame, Theme.Radius.Medium)
	UIKit.stroke(frame, C.Stroke, 1, 0)
	return frame
end

-- Button with hover / press / selection feedback.
-- style: "primary" | "secondary" | "ghost" | "danger"
function UIKit.button(props)
	local style = props.Style or "secondary"
	local palette = {
		primary = { bg = C.Accent, hover = C.AccentDark, text = C.TextOnAccent },
		secondary = { bg = C.Surface, hover = C.SurfaceAlt, text = C.Text },
		ghost = { bg = C.Background, hover = C.Surface, text = C.Text },
		danger = { bg = C.DangerSoft, hover = Color3.fromRGB(248, 214, 214), text = C.Danger },
	}
	local colors = palette[style] or palette.secondary
	local button = UIKit.new("TextButton", {
		Name = props.Name or "Button",
		AutoButtonColor = false,
		BackgroundColor3 = colors.bg,
		BorderSizePixel = 0,
		Size = props.Size or UDim2.fromOffset(120, 36),
		Position = props.Position,
		AnchorPoint = props.AnchorPoint,
		LayoutOrder = props.LayoutOrder or 0,
		Font = props.Font or Theme.Fonts.Medium,
		TextSize = props.TextSize or Theme.TextSize.Body,
		TextColor3 = colors.text,
		Text = props.Text or "",
		TextWrapped = true,
		Parent = props.Parent,
	})
	UIKit.corner(button, props.Radius or Theme.Radius.Small)
	local stroke = nil
	if style ~= "primary" then
		stroke = UIKit.stroke(button, C.Stroke, 1, 0)
	end
	local scale = Instance.new("UIScale")
	scale.Parent = button

	local state = { selected = false, disabled = false, hovering = false }

	local function restColor()
		if state.disabled then
			return C.Disabled
		end
		if state.selected then
			return C.AccentSoft
		end
		return colors.bg
	end

	button.MouseEnter:Connect(function()
		state.hovering = true
		if not state.disabled and not state.selected then
			UIKit.tween(button, Theme.Motion.Fast, { BackgroundColor3 = colors.hover })
		end
	end)
	button.MouseLeave:Connect(function()
		state.hovering = false
		UIKit.tween(button, Theme.Motion.Fast, { BackgroundColor3 = restColor() })
		UIKit.tween(scale, Theme.Motion.Fast, { Scale = 1 })
	end)
	button.MouseButton1Down:Connect(function()
		if not state.disabled then
			UIKit.tween(scale, Theme.Motion.Fast, { Scale = 0.96 })
		end
	end)
	button.MouseButton1Up:Connect(function()
		UIKit.tween(scale, Theme.Motion.Fast, { Scale = 1 })
	end)
	button.Activated:Connect(function()
		if not state.disabled and props.OnClick then
			props.OnClick(button)
		end
	end)

	local api = { Instance = button }
	function api.setSelected(selected: boolean)
		state.selected = selected
		UIKit.tween(button, Theme.Motion.Normal, { BackgroundColor3 = restColor() })
		if stroke then
			UIKit.tween(stroke, Theme.Motion.Normal, { Color = selected and C.Accent or C.Stroke })
		end
	end
	function api.setDisabled(disabled: boolean)
		state.disabled = disabled
		button.TextColor3 = disabled and C.TextMuted or colors.text
		button.BackgroundColor3 = restColor()
	end
	function api.setText(text: string)
		button.Text = text
	end
	return api
end

-- Subtle open: slight slide up + scale in. Frame must contain (or gets) a UIScale.
-- Only one UIScale per object is honoured, so motion reuses FitScale when present
-- and animates relative to its "BaseScale" attribute.
local function getScale(frame: GuiObject)
	local scale = frame:FindFirstChild("FitScale") or frame:FindFirstChild("MotionScale")
	if not scale then
		scale = Instance.new("UIScale")
		scale.Name = "MotionScale"
		scale.Parent = frame
	end
	return scale, (frame:GetAttribute("BaseScale") or 1)
end

function UIKit.open(frame: GuiObject, fromOffsetY: number?)
	local target = frame:GetAttribute("RestPosition")
	if not target then
		target = frame.Position
		frame:SetAttribute("RestPosition", target)
	end
	local scale, base = getScale(frame)
	scale.Scale = base * 0.97
	frame.Position = target + UDim2.fromOffset(0, fromOffsetY or 8)
	frame.Visible = true
	UIKit.tween(scale, Theme.Motion.Normal, { Scale = base })
	UIKit.tween(frame, Theme.Motion.Normal, { Position = target })
end

function UIKit.close(frame: GuiObject, toOffsetY: number?, onDone)
	if not frame.Visible then
		if onDone then
			onDone()
		end
		return
	end
	local target = frame:GetAttribute("RestPosition") or frame.Position
	local scale, base = getScale(frame)
	UIKit.tween(scale, Theme.Motion.Fast, { Scale = base * 0.97 })
	local tween = UIKit.tween(frame, Theme.Motion.Fast, { Position = target + UDim2.fromOffset(0, toOffsetY or 8) })
	tween.Completed:Connect(function()
		frame.Visible = false
		frame.Position = target
		scale.Scale = base
		if onDone then
			onDone()
		end
	end)
end

-- Horizontal ScrollingFrame that also scrolls with the mouse wheel (PC) and touch (mobile).
function UIKit.hScroll(props)
	local frame = UIKit.new("ScrollingFrame", {
		Name = props.Name or "HScroll",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = props.Size,
		Position = props.Position or UDim2.new(),
		ScrollingDirection = Enum.ScrollingDirection.X,
		AutomaticCanvasSize = Enum.AutomaticSize.X,
		CanvasSize = UDim2.new(),
		ScrollBarThickness = 3,
		ScrollBarImageColor3 = C.Stroke,
		ElasticBehavior = Enum.ElasticBehavior.WhenScrollable,
		LayoutOrder = props.LayoutOrder or 0,
		Parent = props.Parent,
	})
	UIKit.list(frame, Enum.FillDirection.Horizontal, props.Spacing or 6, nil, Enum.VerticalAlignment.Center)
	-- Mouse wheel -> horizontal scroll while hovering (children buttons do not block this).
	local hovering = false
	frame.MouseEnter:Connect(function()
		hovering = true
	end)
	frame.MouseLeave:Connect(function()
		hovering = false
	end)
	local connection
	connection = UserInputService.InputChanged:Connect(function(input)
		if not frame.Parent then
			connection:Disconnect()
			return
		end
		if hovering and frame.Visible and input.UserInputType == Enum.UserInputType.MouseWheel then
			local maxX = math.max(0, frame.AbsoluteCanvasSize.X - frame.AbsoluteWindowSize.X)
			local x = math.clamp(frame.CanvasPosition.X - input.Position.Z * 60, 0, maxX)
			UIKit.tween(frame, Theme.Motion.Fast, { CanvasPosition = Vector2.new(x, 0) })
		end
	end)
	return frame
end

function UIKit.vScroll(props)
	local frame = UIKit.new("ScrollingFrame", {
		Name = props.Name or "VScroll",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = props.Size,
		Position = props.Position or UDim2.new(),
		ScrollingDirection = Enum.ScrollingDirection.Y,
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		CanvasSize = UDim2.new(),
		ScrollBarThickness = 3,
		ScrollBarImageColor3 = C.Stroke,
		LayoutOrder = props.LayoutOrder or 0,
		Parent = props.Parent,
	})
	return frame
end

-- Flag display: real asset if FlagAsset is set, otherwise emoji fallback text.
function UIKit.flag(parent: Instance, entry, size: number)
	local holder = UIKit.new("Frame", {
		Name = "Flag",
		BackgroundColor3 = C.SurfaceAlt,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(size * 1.4, size),
		Parent = parent,
	})
	UIKit.corner(holder, 4)
	if entry and type(entry.FlagAsset) == "string" and entry.FlagAsset ~= "" then
		UIKit.new("ImageLabel", {
			BackgroundTransparency = 1,
			Size = UDim2.fromScale(1, 1),
			Image = entry.FlagAsset,
			ScaleType = Enum.ScaleType.Crop,
			Parent = holder,
		})
	else
		UIKit.new("TextLabel", {
			BackgroundTransparency = 1,
			Size = UDim2.fromScale(1, 1),
			Text = entry and entry.EmojiFallback or "?",
			TextScaled = true,
			Font = Theme.Fonts.Regular,
			TextColor3 = C.Text,
			Parent = holder,
		})
	end
	return holder
end

-- Scale a centered dialog down on small screens (mobile) so it never covers the whole screen.
function UIKit.autoScale(frame: GuiObject, designWidth: number, designHeight: number)
	local scale = Instance.new("UIScale")
	scale.Name = "FitScale"
	scale.Parent = frame
	local function update()
		local camera = Workspace.CurrentCamera
		if not camera then
			return
		end
		local viewport = camera.ViewportSize
		local s = math.max(math.min((viewport.X - 24) / designWidth, (viewport.Y - 96) / designHeight, 1), 0.55)
		frame:SetAttribute("BaseScale", s)
		scale.Scale = s
	end
	update()
	local camera = Workspace.CurrentCamera
	if camera then
		camera:GetPropertyChangedSignal("ViewportSize"):Connect(update)
	end
	return scale
end

return UIKit
