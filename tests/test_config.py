
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
CONFIG = SRC / "ReplicatedStorage" / "Shared" / "Config"


def load_json(name):
    with open(CONFIG / name, encoding="utf-8") as f:
        return json.load(f)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class GameConfigTests(unittest.TestCase):
    def setUp(self):
        self.game = load_json("GameConfig.json")

    def test_exactly_three_slots(self):
        slots = self.game["Slots"]
        self.assertEqual(self.game["SlotCount"], 3)
        self.assertEqual(len(slots), 3)
        self.assertEqual([s["Unlocked"] for s in slots], [True, False, False])
        self.assertEqual([s["Label"] for s in slots], ["FREE", "LOCKED", "LOCKED"])

    def test_empty_country_defaults(self):
        empty = self.game["EmptyCountry"]
        for key in ("Money", "Oil", "Fuel", "Steel", "Supplies", "Population", "Workers", "HousingCapacity"):
            self.assertEqual(empty[key], 0, key)
        for key in ("Buildings", "Roads", "Military"):
            self.assertEqual(empty[key], {}, key)


class BuildingConfigTests(unittest.TestCase):
    def setUp(self):
        self.buildings = load_json("BuildingConfig.json")["Buildings"]
        self.placement = load_json("PlacementConfig.json")
        self.models = read("src/ReplicatedStorage/Shared/Modules/BuildingModels.luau")

    def test_three_residential_types(self):
        ids = [b["Id"] for b in self.buildings if b["Category"] == "Housing"]
        self.assertEqual(ids, ["SmallHouse", "MediumHouse", "LargeHouse"])

    def test_building_fields(self):
        grid = self.placement["GridSize"]
        for b in self.buildings:
            self.assertGreater(b["HousingCapacity"], 0)
            self.assertGreater(b["BuildTimeSeconds"], 0)
            self.assertEqual(len(b["Footprint"]), 2)
            for side in b["Footprint"]:
                self.assertEqual(side % grid, 0, b["Id"])
                self.assertLessEqual(side, 24, "buildings must stay small")

    def test_variants_exist_in_models(self):
        defined = set(re.findall(r"^Variants\.(\w+) = function", self.models, re.M))
        for b in self.buildings:
            self.assertGreaterEqual(len(b["Variants"]), 4, b["Id"])
            for v in b["Variants"]:
                self.assertIn(v, defined)

    def test_no_permanent_labels_on_buildings(self):
        self.assertNotIn("BillboardGui", self.models)


class RoadAndPlacementTests(unittest.TestCase):
    def setUp(self):
        self.roads = load_json("RoadConfig.json")
        self.placement = load_json("PlacementConfig.json")

    def test_road_types(self):
        ids = [t["Id"] for t in self.roads["Types"]]
        self.assertEqual(ids, ["Straight", "Corner", "TJunction", "Crossroad"])
        expected = {"Straight": 2, "Corner": 2, "TJunction": 3, "Crossroad": 4}
        for t in self.roads["Types"]:
            self.assertEqual(len(t["Openings"]), expected[t["Id"]])
            self.assertTrue(set(t["Openings"]) <= {"N", "E", "S", "W"})

    def test_road_tile_matches_grid(self):
        self.assertEqual(self.roads["TileSize"], self.placement["RoadTileSize"])
        self.assertEqual(self.placement["RoadTileSize"] % self.placement["GridSize"], 0)
        self.assertLess(self.roads["RoadWidth"], self.roads["TileSize"])

    def test_placement_config(self):
        self.assertGreater(self.placement["MaxRoadDistance"], 0)
        self.assertTrue(self.placement["RequireRoadAccess"])
        game = load_json("GameConfig.json")
        self.assertEqual(game["Territory"]["Size"] % self.placement["RoadTileSize"], 0)


class MenuAndTechTests(unittest.TestCase):
    def test_build_menu_categories(self):
        cats = [c["Id"] for c in load_json("BuildMenuConfig.json")["Categories"]]
        self.assertEqual(
            cats,
            ["Roads", "Housing", "Services", "Commercial", "Agriculture", "Resources", "Industrial", "Other"],
        )

    def test_technology_branches(self):
        branches = load_json("TechnologyConfig.json")["Branches"]
        self.assertEqual([b["DisplayName"] for b in branches], ["USSR / Russia", "USA", "Germany"])


if __name__ == "__main__":
    unittest.main()
