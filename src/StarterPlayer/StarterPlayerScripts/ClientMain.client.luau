-- ClientMain: the single client entry point.
-- Client responsibilities: input, UI, preview. Everything permanent is requested from the server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local mainUI = playerGui:WaitForChild("MainUI")

mainUI.ResetOnSpawn = false
mainUI.IgnoreGuiInset = false
mainUI.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
pcall(function()
	mainUI.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
end)

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local Remotes = ReplicatedStorage:WaitForChild("Remotes")

local Controllers = script.Parent:WaitForChild("Controllers")
local ClientState = require(Controllers:WaitForChild("ClientState"))
local PlacementController = require(Controllers:WaitForChild("PlacementController"))

local Screens = mainUI:WaitForChild("Screens")
local Toast = require(Screens:WaitForChild("Toast"))
local SlotScreen = require(Screens:WaitForChild("SlotScreen"))
local CreateStateScreen = require(Screens:WaitForChild("CreateStateScreen"))
local HUD = require(Screens:WaitForChild("HUD"))
local BuildMenu = require(Screens:WaitForChild("BuildMenu"))
local PlacementBar = require(Screens:WaitForChild("PlacementBar"))

local function remote(name: string)
	return Remotes:WaitForChild(name)
end

local function invoke(name: string, ...)
	local args = table.pack(...)
	local ok, result = pcall(function()
		return remote(name):InvokeServer(table.unpack(args, 1, args.n))
	end)
	if not ok then
		return { ok = false, error = "Connection problem" }
	end
	if type(result) ~= "table" then
		return { ok = false, error = "Unexpected server response" }
	end
	return result
end

player.CameraMaxZoomDistance = math.max(player.CameraMaxZoomDistance, 180)

local toast = Toast.new(mainUI)
local slotScreen, createScreen, hud, buildMenu, placementBar

local function showSlots()
	local profile = invoke(Constants.Remotes.GetProfile)
	if not profile.ok then
		toast:show(profile.error or "Could not load slots", "error")
		task.delay(2, showSlots)
		return
	end
	hud:hide()
	slotScreen:show(profile)
end

local function enterGame(result)
	if not result.ok then
		toast:show(result.error or "Could not enter state", "error")
		return false
	end
	slotScreen:hide()
	if result.state then
		ClientState.set(result.state)
	end
	hud:show()
	hud:update(ClientState.snapshot)
	toast:show("Welcome to " .. tostring(ClientState.snapshot.Name or "your state"), "success")
	return true
end

slotScreen = SlotScreen.new(mainUI, {
	onCreate = function(index)
		slotScreen:hide()
		createScreen:show(index)
	end,
	onPlay = function(index)
		enterGame(invoke(Constants.Remotes.LoadSlot, index))
	end,
	onDelete = function(index)
		local result = invoke(Constants.Remotes.DeleteSlot, index)
		if result.ok then
			toast:show("Slot " .. index .. " deleted")
		else
			toast:show(result.error or "Delete failed", "error")
		end
		showSlots()
	end,
})

createScreen = CreateStateScreen.new(mainUI, {
	onSubmit = function(index, payload)
		local result = invoke(Constants.Remotes.CreateCountry, index, payload)
		if result.ok then
			enterGame(result)
		end
		return result
	end,
	onCancel = function()
		showSlots()
	end,
})

local function exitPlacement()
	PlacementController.cancel()
	placementBar:hide()
	hud:setHammerVisible(true)
end

buildMenu = BuildMenu.new(mainUI, {
	onSelect = function(kind, id)
		hud:setHammerVisible(false)
		PlacementController.start(kind, id)
		placementBar:show()
	end,
	onClose = function()
		hud:setHammerVisible(true)
	end,
})

placementBar = PlacementBar.new(mainUI, {
	onStyle = function()
		PlacementController.cycleVariant()
	end,
	onRotate = function()
		PlacementController.rotate()
	end,
	onPlace = function()
		PlacementController.confirm()
	end,
	onDone = function()
		exitPlacement()
		buildMenu:show()
		hud:setHammerVisible(false)
	end,
})

hud = HUD.new(mainUI, {
	onHammer = function()
		hud:closeMenu()
	end,
	onOpenBuild = function()
		hud:setHammerVisible(false)
		buildMenu:show()
	end,
	onSave = function()
		local result = invoke(Constants.Remotes.SaveNow)
		if result.ok and result.persistent then
			toast:show("Saved", "success")
		elseif result.ok then
			toast:show("Saving is off in this session", "error")
		else
			toast:show(result.error or "Save failed", "error")
		end
	end,
	onChangeSlot = function()
		exitPlacement()
		buildMenu.panel.Visible = false
		local result = invoke(Constants.Remotes.LeaveState)
		if result.ok then
			ClientState.set({ Active = false })
			showSlots()
		else
			toast:show(result.error or "Could not leave", "error")
		end
	end,
})

PlacementController.onStatus(function(status)
	if status.Active then
		placementBar:update(status)
	else
		placementBar:hide()
		if not buildMenu:isOpen() and ClientState.snapshot.Active then
			hud:setHammerVisible(true)
		end
	end
end)

PlacementController.onResult(function(success, message)
	if not success then
		toast:show(message, "error")
	end
end)

remote(Constants.Remotes.StateChanged).OnClientEvent:Connect(function(snapshot)
	ClientState.set(snapshot)
end)

remote(Constants.Remotes.Notify).OnClientEvent:Connect(function(payload)
	if type(payload) == "table" and type(payload.Text) == "string" then
		toast:show(payload.Text, payload.Kind)
	end
end)

ClientState.onChanged(function(snapshot)
	if snapshot.Active then
		hud:update(snapshot)
	end
end)

pcall(function()
	StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false)
end)

showSlots()
