# WAR STATE - DEVELOPMENT_ROADMAP.md

> Future plan only. What exists today is in PROJECT.md. Do not mark anything here as done; move it to PROJECT.md when it ships.

## Phase 1 - First playable foundation (current)
Save slots, country creation, flag selection (195), technology selection, empty world, residential buildings,
construction, logical population, roads, road access, build menu.

## Phase 2 - Stabilize the city builder
- Demolish / undo for roads and buildings (with refunds once economy exists)
- Road auto-tiling (choose Straight/Corner/T/Cross automatically from neighbours)
- Drag-to-place road lines
- DataStore session locking + save versioning/migrations
- Offline construction progress (timestamp based)
- Verified flag image assets (only real, checked Roblox asset ids)

## Phase 3 - Services and commerce
- Services (clinic, school, police) and Commercial (shops)
- Civilian trips on the road graph: House -> Road -> Shop -> Road -> House, House -> Road -> Service -> House
- A small number of visual cars/NPCs driven by logical demand (no mass NPC simulation)

## Phase 4 - Resources and industry
- Oil Well -> Crude Oil -> Refinery -> Fuel
- Steel, Supplies production
- Factory -> Road -> Truck -> Warehouse
- Logistics vehicles: Truck, Freight Truck, Fuel Truck (after road graph pathfinding is stable)

## Phase 5 - Research
- Time-based research: ResearchTime, Requirements, Unlocks
- Branch-specific equipment lines for USSR / Russia, USA, Germany (no doctrine system)

## Phase 6 - Military layer
- Military data + UI (units, production queues) built on top of industry and logistics
- Reserved modules: Reconnaissance, Satellites, UAV, Aircraft, Helicopters, Electronic Warfare

## Phase 7 - Slots 2 and 3
- Unlock mechanism (monetization design decided later)

## Engineering rules for every phase
- Server authority for all permanent state; client = input, UI, preview
- Config in JSON under Shared/Config; no magic numbers in systems
- Keep build_war_state.py idempotent; update PROJECT.md on every major change
