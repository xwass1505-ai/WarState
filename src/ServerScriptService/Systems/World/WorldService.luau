-- WorldService: generates the simple flat green territory (one plot per active country)
-- and the per-plot Buildings/Roads folders. NO buildings, roads, citizens or city are pre-placed.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local Plots = require(Shared:WaitForChild("Modules"):WaitForChild("Plots"))

local WorldService = {}
WorldService.Name = "WorldService"

local plotOwners = {} -- [index] = Player
local playerPlots = {} -- [Player] = index

local function ensureFolder(parent: Instance, name: string): Folder
	local existing = parent:FindFirstChild(name)
	if existing and existing:IsA("Folder") then
		return existing
	end
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = parent
	return folder
end

local function rootFolders()
	return {
		Map = ensureFolder(Workspace, "Map"),
		Buildings = ensureFolder(Workspace, "Buildings"),
		Roads = ensureFolder(Workspace, "Roads"),
		Vehicles = ensureFolder(Workspace, "Vehicles"),
		NPCs = ensureFolder(Workspace, "NPCs"),
	}
end

local function color(t)
	return Color3.new(t[1], t[2], t[3])
end

local function createTerritory(index: number, owner: Player)
	local folders = rootFolders()
	local bounds = Plots.getBounds(index)
	local t = GameConfig.Territory
	local name = "Territory_" .. index
	local existing = folders.Map:FindFirstChild(name)
	if existing then
		existing:Destroy()
	end
	local territory = Instance.new("Model")
	territory.Name = name
	territory:SetAttribute(Constants.Attributes.PlotIndex, index)
	territory:SetAttribute(Constants.Attributes.OwnerUserId, owner.UserId)

	local ground = Instance.new("Part")
	ground.Name = "Ground"
	ground.Anchored = true
	ground.CanCollide = true
	ground.Size = Vector3.new(t.Size, t.Thickness, t.Size)
	ground.CFrame = CFrame.new(bounds.centerX, bounds.surfaceY - t.Thickness / 2, bounds.centerZ)
	ground.Color = color(t.Color)
	ground.Material = Enum.Material.Grass
	ground.TopSurface = Enum.SurfaceType.Smooth
	ground.BottomSurface = Enum.SurfaceType.Smooth
	ground:SetAttribute(Constants.Attributes.PlotIndex, index)
	ground.Parent = territory

	-- Thin low border so the territory edge is readable (not a wall, does not collide).
	local border = t.BorderWidth
	local borderColor = color(t.BorderColor)
	local sides = {
		{ Vector3.new(t.Size, 0.1, border), Vector3.new(0, 0, -t.Size / 2 + border / 2) },
		{ Vector3.new(t.Size, 0.1, border), Vector3.new(0, 0, t.Size / 2 - border / 2) },
		{ Vector3.new(border, 0.1, t.Size), Vector3.new(-t.Size / 2 + border / 2, 0, 0) },
		{ Vector3.new(border, 0.1, t.Size), Vector3.new(t.Size / 2 - border / 2, 0, 0) },
	}
	for i, side in ipairs(sides) do
		local p = Instance.new("Part")
		p.Name = "Border" .. i
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.Size = side[1]
		p.CFrame = CFrame.new(bounds.centerX, bounds.surfaceY + 0.05, bounds.centerZ) + side[2]
		p.Color = borderColor
		p.Material = Enum.Material.SmoothPlastic
		p.Parent = territory
	end
	territory.PrimaryPart = ground
	territory.Parent = folders.Map

	for _, key in ipairs({ "Buildings", "Roads" }) do
		local plotFolderName = "Plot_" .. index
		local old = folders[key]:FindFirstChild(plotFolderName)
		if old then
			old:Destroy()
		end
		local folder = Instance.new("Folder")
		folder.Name = plotFolderName
		folder:SetAttribute(Constants.Attributes.PlotIndex, index)
		folder:SetAttribute(Constants.Attributes.OwnerUserId, owner.UserId)
		folder.Parent = folders[key]
	end
end

local function destroyPlot(index: number)
	local folders = rootFolders()
	local names = { { folders.Map, "Territory_" .. index }, { folders.Buildings, "Plot_" .. index }, { folders.Roads, "Plot_" .. index } }
	for _, pair in ipairs(names) do
		local inst = pair[1]:FindFirstChild(pair[2])
		if inst then
			inst:Destroy()
		end
	end
end

function WorldService.getPlotIndex(player: Player): number?
	return playerPlots[player]
end

function WorldService.getBounds(player: Player)
	local index = playerPlots[player]
	if not index then
		return nil
	end
	return Plots.getBounds(index)
end

function WorldService.getPlotFolder(player: Player, kind: string): Folder?
	local index = playerPlots[player]
	if not index then
		return nil
	end
	local root = Workspace:FindFirstChild(kind)
	return root and root:FindFirstChild("Plot_" .. index) or nil
end

local function spawnCFrame(bounds)
	return CFrame.new(bounds.centerX, bounds.surfaceY + 4, bounds.centerZ + 24)
end

function WorldService.teleportToPlot(player: Player)
	local bounds = WorldService.getBounds(player)
	local character = player.Character
	if bounds and character then
		character:PivotTo(spawnCFrame(bounds))
	end
end

function WorldService.enter(player: Player): (boolean, string?)
	if playerPlots[player] then
		return true, nil
	end
	local index = nil
	for i = 1, Plots.maxPlots() do
		if plotOwners[i] == nil then
			index = i
			break
		end
	end
	if not index then
		return false, "Server is full of states. Try another server."
	end
	plotOwners[index] = player
	playerPlots[player] = index
	createTerritory(index, player)
	player:SetAttribute(Constants.Attributes.PlotIndex, index)
	WorldService.teleportToPlot(player)
	return true, nil
end

function WorldService.leave(player: Player)
	local index = playerPlots[player]
	if not index then
		return
	end
	destroyPlot(index)
	plotOwners[index] = nil
	playerPlots[player] = nil
	player:SetAttribute(Constants.Attributes.PlotIndex, nil)
end

function WorldService.init(_services)
	rootFolders()
end

function WorldService.start()
	Players.PlayerAdded:Connect(function(player)
		player.CharacterAdded:Connect(function()
			task.defer(function()
				if playerPlots[player] then
					WorldService.teleportToPlot(player)
				end
			end)
		end)
	end)
	for _, player in ipairs(Players:GetPlayers()) do
		player.CharacterAdded:Connect(function()
			task.defer(function()
				if playerPlots[player] then
					WorldService.teleportToPlot(player)
				end
			end)
		end)
	end
	Players.PlayerRemoving:Connect(function(player)
		WorldService.leave(player)
	end)
end

return WorldService
