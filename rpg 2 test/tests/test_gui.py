import os
import random
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtWidgets import QApplication

import world
from characters import Character
from enemies import create_enemy
from gui import BattleStage, GameWindow, LauncherWindow
from gui import NewGameDialog
from races import RACES
from party import Party


class PyQtGameTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        party = Party()
        party.add_member(Character("Aster", "Warrior", 60, 0, 10, 5))
        self.window = GameWindow(party)

    def tearDown(self):
        self.window.close()

    def test_game_window_builds_and_updates_through_shared_map_engine(self):
        self.assertEqual(world.current_map_name, "world_map")
        with patch("world.check_for_encounter", return_value=False):
            self.window.move_player("d")

        self.assertEqual((world.player_x, world.player_y), (1, 0))
        self.assertIn("Shattered", self.window.location_title.text())

    def test_world_sprite_canvas_renders_to_qimage(self):
        canvas = self.window.map_canvas
        canvas.resize(640, 560)
        image = QImage(
            canvas.size(),
            QImage.Format.Format_ARGB32
        )
        image.fill(0)
        painter = QPainter(image)
        canvas.render(painter)
        painter.end()

        self.assertFalse(image.isNull())
        self.assertNotEqual(image.pixelColor(20, 20).alpha(), 0)

    def test_battle_stage_animates_pixel_sprites_and_hit_effects(self):
        enemy = create_enemy("Goblin")
        stage = BattleStage(self.window.party, [enemy])
        stage.resize(640, 320)
        stage.impact(enemy.name, 12)
        stage._animate()

        image = QImage(stage.size(), QImage.Format.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        stage.render(painter)
        painter.end()

        self.assertEqual(len(stage.effects), 1)
        self.assertFalse(image.isNull())

    def test_launcher_and_game_window_are_native_qt_windows(self):
        launcher = LauncherWindow()
        try:
            self.assertEqual(launcher.windowTitle(), "Shattered Marches")
            self.assertEqual(self.window.windowTitle(), "Shattered Marches")
        finally:
            launcher.close()

    def test_custom_party_dialog_builds_race_and_custom_class(self):
        dialog = NewGameDialog()
        try:
            dialog.name_fields[0].setCurrentText("Nova")
            dialog.race_fields[0].setCurrentText("Elf")
            dialog.job_fields[0].setCurrentText("Custom")
            dialog.custom_name_fields[0].setCurrentText("Arcanist")
            dialog.custom_stats[0]["strength"].setValue(12)
            dialog.ability_fields[0].setCurrentText("Fire")

            party = dialog.build_party()
            member = party.members[0]
            self.assertEqual(member.name, "Nova")
            self.assertEqual(member.race, "Elf")
            self.assertEqual(member.job.name, "Arcanist")
            self.assertEqual(member.strength, 12)
            self.assertTrue(any(spell.name == "Fire" for spell in member.spells))
            self.assertIn("Elf", RACES)
        finally:
            dialog.close()

    def test_50_custom_class_permutations_build_safely(self):
        races = list(RACES)
        abilities = (
            "Power Strike", "Guard Stance", "Backstab", "First Aid",
            "Protect", "Fire", "Cure", "Aimed Shot", "Holy Strike"
        )

        for permutation in range(50):
            rng = random.Random(202612300 + permutation)
            dialog = NewGameDialog()
            try:
                for index in range(4):
                    race = rng.choice(races)
                    ability = rng.choice(abilities)
                    dialog.name_fields[index].setCurrentText(
                        f"Adventurer {permutation + 1}-{index + 1}"
                    )
                    dialog.race_fields[index].setCurrentText(race)
                    dialog.job_fields[index].setCurrentText("Custom")
                    dialog.custom_name_fields[index].setCurrentText(
                        f"Class {permutation + 1}-{index + 1}"
                    )
                    dialog.custom_stats[index]["max_hp"].setValue(rng.randint(35, 55))
                    dialog.custom_stats[index]["max_mp"].setValue(rng.randint(0, 25))
                    dialog.custom_stats[index]["strength"].setValue(rng.randint(1, 14))
                    dialog.custom_stats[index]["defense"].setValue(rng.randint(1, 10))
                    dialog.ability_fields[index].setCurrentText(ability)

                party = dialog.build_party()
                self.assertEqual(len(party.members), 4)
                for index, member in enumerate(party.members):
                    self.assertEqual(
                        member.name,
                        f"Adventurer {permutation + 1}-{index + 1}"
                    )
                    self.assertIn(member.race, RACES)
                    self.assertGreater(member.max_hp, 0)
                    self.assertGreaterEqual(member.max_mp, 0)
                    self.assertGreater(member.strength, 0)
                    self.assertGreaterEqual(member.defense, 0)
                    self.assertTrue(member.spells)
            finally:
                dialog.close()


if __name__ == "__main__":
    unittest.main()
