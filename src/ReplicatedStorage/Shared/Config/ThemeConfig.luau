-- ThemeConfig: White + Light Blue UI theme. Tweak visuals here only.

local Theme = {}

Theme.Colors = {
	Background = Color3.fromRGB(255, 255, 255),
	Surface = Color3.fromRGB(246, 250, 255),
	SurfaceAlt = Color3.fromRGB(234, 243, 253),
	Accent = Color3.fromRGB(84, 156, 230),
	AccentSoft = Color3.fromRGB(214, 233, 252),
	AccentDark = Color3.fromRGB(52, 116, 190),
	Text = Color3.fromRGB(28, 40, 56),
	TextMuted = Color3.fromRGB(108, 124, 146),
	TextOnAccent = Color3.fromRGB(255, 255, 255),
	Stroke = Color3.fromRGB(206, 223, 242),
	Danger = Color3.fromRGB(214, 88, 88),
	DangerSoft = Color3.fromRGB(252, 232, 232),
	Disabled = Color3.fromRGB(226, 231, 238),
	Success = Color3.fromRGB(76, 170, 120),
}

Theme.Fonts = {
	Regular = Enum.Font.Gotham,
	Medium = Enum.Font.GothamMedium,
	Bold = Enum.Font.GothamBold,
}

Theme.TextSize = {
	Small = 12,
	Body = 14,
	Title = 18,
	Header = 22,
}

Theme.Radius = {
	Small = 8,
	Medium = 12,
	Pill = 999,
}

Theme.Motion = {
	Fast = 0.12,
	Normal = 0.2,
	Slow = 0.28,
	Style = Enum.EasingStyle.Quad,
	Direction = Enum.EasingDirection.Out,
}

return Theme
