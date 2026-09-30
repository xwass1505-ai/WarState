-- Types: shared Luau type definitions (documentation + type checking only, no runtime logic).

export type BuildState = "PLANNED" | "UNDER_CONSTRUCTION" | "COMPLETED"

export type BuildingRecord = {
	Id: string,
	Type: string,
	Variant: string,
	X: number, -- plot-local center X
	Z: number, -- plot-local center Z
	Rotation: number, -- 0..3 quarter turns clockwise
	State: BuildState,
	PlannedElapsed: number,
	Progress: number, -- seconds of construction completed
	CreatedAt: number,
}

export type RoadSegment = {
	RoadId: string,
	Type: string, -- Straight | Corner | TJunction | Crossroad
	Rotation: number,
	Ix: number,
	Iz: number,
	Position: { X: number, Z: number }, -- plot-local tile center
	Neighbours: { string }, -- mutually connected RoadIds (graph edges)
	Adjacent: { string }, -- touching RoadIds (connected or not)
	Connected: boolean,
}

export type Country = {
	SchemaVersion: number,
	SlotIndex: number,
	Name: string,
	FlagId: string,
	Continent: string,
	TechnologyBranch: string,
	CreatedAt: number,
	Money: number,
	Oil: number,
	Fuel: number,
	Steel: number,
	Supplies: number,
	Population: number,
	Workers: number,
	HousingCapacity: number,
	Buildings: { [string]: BuildingRecord },
	Roads: { [string]: RoadSegment },
	Military: { [string]: any },
	NextBuildingId: number,
	NextRoadId: number,
}

export type SlotSummary = {
	Index: number,
	Locked: boolean,
	Empty: boolean,
	Name: string?,
	FlagId: string?,
	TechnologyBranch: string?,
	Population: number?,
}

return {}
