
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


REQUIRED_FILES = [
    "default.project.json",
    "src/ServerScriptService/ServerMain.server.luau",
    "src/ServerScriptService/Systems/Data/DataService.luau",
    "src/ServerScriptService/Systems/Country/CountryService.luau",
    "src/ServerScriptService/Systems/World/WorldService.luau",
    "src/ServerScriptService/Systems/Buildings/BuildingService.luau",
    "src/ServerScriptService/Systems/Construction/ConstructionService.luau",
    "src/ServerScriptService/Systems/Population/PopulationService.luau",
    "src/ServerScriptService/Systems/Roads/RoadService.luau",
    "src/ServerScriptService/Systems/Resources/ResourceService.luau",
    "src/ServerScriptService/Systems/Research/ResearchService.luau",
    "src/ServerScriptService/Systems/Production/ProductionService.luau",
    "src/ServerScriptService/Systems/Economy/EconomyService.luau",
    "src/ServerScriptService/Systems/Military/MilitaryService.luau",
    "src/ServerScriptService/Tests/RuntimeSelfTest.server.luau",
    "src/ReplicatedStorage/Shared/Constants/Constants.luau",
    "src/ReplicatedStorage/Shared/Types/Types.luau",
    "src/ReplicatedStorage/Shared/Config/GameConfig.json",
    "src/ReplicatedStorage/Shared/Config/BuildingConfig.json",
    "src/ReplicatedStorage/Shared/Config/RoadConfig.json",
    "src/ReplicatedStorage/Shared/Config/PlacementConfig.json",
    "src/ReplicatedStorage/Shared/Config/BuildMenuConfig.json",
    "src/ReplicatedStorage/Shared/Config/TechnologyConfig.json",
    "src/ReplicatedStorage/Shared/Config/CountryRegistry.json",
    "src/ReplicatedStorage/Shared/Config/ThemeConfig.luau",
    "src/ReplicatedStorage/Shared/Modules/GridMath.luau",
    "src/ReplicatedStorage/Shared/Modules/PlacementRules.luau",
    "src/ReplicatedStorage/Shared/Modules/RoadGraph.luau",
    "src/ReplicatedStorage/Shared/Modules/BuildingModels.luau",
    "src/ReplicatedStorage/Shared/Modules/RoadModels.luau",
    "src/ReplicatedStorage/Shared/Modules/Countries.luau",
    "src/ReplicatedStorage/Shared/Modules/DefaultCountry.luau",
    "src/ReplicatedStorage/Shared/Modules/Plots.luau",
    "src/StarterPlayer/StarterPlayerScripts/ClientMain.client.luau",
    "src/StarterPlayer/StarterPlayerScripts/Controllers/ClientState.luau",
    "src/StarterPlayer/StarterPlayerScripts/Controllers/PlacementController.luau",
    "src/StarterGui/MainUI/Components/UIKit.luau",
    "src/StarterGui/MainUI/Screens/SlotScreen.luau",
    "src/StarterGui/MainUI/Screens/CreateStateScreen.luau",
    "src/StarterGui/MainUI/Screens/HUD.luau",
    "src/StarterGui/MainUI/Screens/BuildMenu.luau",
    "src/StarterGui/MainUI/Screens/PlacementBar.luau",
    "src/StarterGui/MainUI/Screens/Toast.luau",
    "DEVELOPMENT_ROADMAP.md",
    "AGENTS.md",
]

REQUIRED_DIRS = [
    "src/ReplicatedStorage/Shared/Config",
    "src/ReplicatedStorage/Shared/Constants",
    "src/ReplicatedStorage/Shared/Types",
    "src/ReplicatedStorage/Shared/Modules",
    "src/ReplicatedStorage/Assets",
    "src/Workspace/Map",
    "src/Workspace/Buildings",
    "src/Workspace/Roads",
    "src/Workspace/Vehicles",
    "src/Workspace/NPCs",
]


class StructureTests(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [f for f in REQUIRED_FILES if not (ROOT / f).is_file()]
        self.assertEqual(missing, [], "Missing files: %s" % missing)

    def test_required_dirs_exist(self):
        missing = [d for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
        self.assertEqual(missing, [])

    def test_project_json_paths_exist(self):
        project = json.loads(read("default.project.json"))
        self.assertEqual(project["tree"]["$className"], "DataModel")
        bad = []

        def walk(node):
            for key, value in node.items():
                if key == "$path" and not (ROOT / value).exists():
                    bad.append(value)
                elif isinstance(value, dict) and not key.startswith("$"):
                    walk(value)

        walk(project["tree"])
        self.assertEqual(bad, [])

    def test_services_do_not_wipe_existing_place(self):
        tree = json.loads(read("default.project.json"))["tree"]
        for service in ("ReplicatedStorage", "ServerScriptService", "StarterPlayer", "StarterGui", "Workspace"):
            self.assertIn(service, tree)
            self.assertNotIn("$path", tree[service], "%s must not be mapped wholesale" % service)
            self.assertTrue(tree[service].get("$ignoreUnknownInstances"), service)

    def test_remotes_match_constants(self):
        tree = json.loads(read("default.project.json"))["tree"]
        remotes = {k for k in tree["ReplicatedStorage"]["Remotes"] if not k.startswith("$")}
        constants = read("src/ReplicatedStorage/Shared/Constants/Constants.luau")
        block = re.search(r"Constants\.Remotes = \{(.*?)\n\}", constants, re.S).group(1)
        declared = set(re.findall(r'^\t(\w+) = "\1",$', block, re.M))
        self.assertEqual(remotes, declared)


if __name__ == "__main__":
    unittest.main()
