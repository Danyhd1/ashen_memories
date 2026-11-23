import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import world
from characters import Character
from party import Party
from save import load_game, save_game


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class WorldEventTests(unittest.TestCase):

    def setUp(self):
        self.party = Party()
        self.hero = Character("Tala", "White Mage", 40, 20, 4, 2)
        self.party.add_member(self.hero)
        world.load_map("world_map")

    def test_world_map_is_larger_and_every_event_has_a_visible_marker(self):
        with open(PROJECT_ROOT / "maps" / "world_map.json", encoding="utf-8") as file:
            map_data = json.load(file)
        with open(PROJECT_ROOT / "data" / "world_events.json", encoding="utf-8") as file:
            events = json.load(file)

        self.assertGreaterEqual(len(map_data["tiles"]), 30)
        self.assertTrue(all(len(row) == 30 for row in map_data["tiles"]))

        for event in events.values():
            tile = map_data["tiles"][event["y"]][event["x"]]
            self.assertEqual(tile, "?", event["name"])

    def test_location_cache_grants_items_once(self):
        world.player_x = 2
        world.player_y = 1

        with patch("builtins.print"):
            self.assertTrue(world.handle_location_event(self.party))
            self.assertFalse(world.handle_location_event(self.party))

        self.assertEqual(
            [item.name for item in self.hero.inventory],
            ["Hi-Potion", "Hi-Potion"]
        )
        self.assertIn("forest_herbalist_cache", self.party.discovered_events)

    def test_exploration_triggers_event_when_player_enters_location(self):
        with (
            patch("builtins.input", side_effect=["s", "d", "d", "q"]),
            patch("builtins.print"),
            patch("world.check_for_encounter", return_value=False)
        ):
            world.explore(self.party)

        self.assertEqual((world.player_x, world.player_y), (2, 1))
        self.assertIn("forest_herbalist_cache", self.party.discovered_events)
        self.assertEqual(
            [item.name for item in self.hero.inventory],
            ["Hi-Potion", "Hi-Potion"]
        )

    def test_shrine_restores_party_and_is_recorded(self):
        world.player_x = 12
        world.player_y = 11
        self.hero.hp = 3
        self.hero.mp = 1

        with patch("builtins.print"):
            world.handle_location_event(self.party)

        self.assertEqual(self.hero.hp, self.hero.max_hp)
        self.assertEqual(self.hero.mp, self.hero.max_mp)
        self.assertIn("mountain_waystone", self.party.discovered_events)

    def test_fixed_ambush_only_marks_event_after_victory(self):
        world.player_x = 8
        world.player_y = 8
        with (
            patch("world.battle", return_value=False) as battle_mock,
            patch("builtins.print")
        ):
            self.assertTrue(world.handle_location_event(self.party))
            self.assertNotIn("graveyard_ambush", self.party.discovered_events)

            battle_mock.return_value = True
            world.handle_location_event(self.party)

        self.assertIn("graveyard_ambush", self.party.discovered_events)
        self.assertEqual(battle_mock.call_args.kwargs["enemies"][0].name, "Wraith")

    def test_discovered_location_event_is_saved_and_loaded(self):
        self.party.discovered_events.append("forest_herbalist_cache")
        previous_directory = os.getcwd()

        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with patch("builtins.print"):
                    save_game(self.party)
                    loaded = load_game()
            finally:
                os.chdir(previous_directory)

        self.assertEqual(
            loaded.discovered_events,
            ["forest_herbalist_cache"]
        )


if __name__ == "__main__":
    unittest.main()
