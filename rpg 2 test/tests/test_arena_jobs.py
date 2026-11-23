import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arena import create_arena_boss, load_arena_challenges
from characters import Character
from items import Equipment, create_item
from party import Party
from quests import Quest, get_quest_definition
from save import load_game, save_game
from town import change_jobs
from jobs import BASE_CLASS_TEMPLATES
from magic import (
    get_spell_level_limit,
    get_spell_slots,
    register_spell,
    register_ability,
)
from items import create_item
from stronghold import (
    STRONGHOLD_TYPES,
    STRONGHOLD_IMPROVEMENTS,
    Stronghold,
)
from crafting import (
    MATERIALS,
    calculate_role_bonuses,
    has_materials,
    consume_materials,
    recipe_catalog,
)
from blacksmith import (
    ARMOR_TEMPLATES,
    WEAPON_TEMPLATES,
    MATERIALS,
    craft_weapon,
    craft_armor,
    get_level_tier,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ArenaAndJobProgressionTests(unittest.TestCase):

    def setUp(self):
        self.party = Party()
        self.hero = Character("Kestrel", "Warrior", 60, 0, 10, 5)
        self.party.add_member(self.hero)

    def test_stronghold_types_and_200_improvements_exist(self):
        self.assertEqual(
            set(STRONGHOLD_TYPES),
            {"Hideout", "Fortress", "Temple", "Academy", "Estate"}
        )
        self.assertEqual(len(STRONGHOLD_IMPROVEMENTS), 200)
        stronghold = Stronghold("Moon Hall", "Temple")
        self.assertEqual(stronghold.stronghold_type, "Temple")

    def test_stronghold_install_uninstall_and_serialization(self):
        stronghold = Stronghold("Stone Keep", "Fortress")
        improvement = next(
            item for item in STRONGHOLD_IMPROVEMENTS
            if stronghold.can_install(item)
        )
        installed = stronghold.install(improvement.id, improvement.cost)
        self.assertIsNotNone(installed)
        self.assertIn(improvement.id, stronghold.installed)
        restored = Stronghold.from_dict(stronghold.to_dict())
        self.assertEqual(restored.name, "Stone Keep")
        self.assertEqual(restored.installed, stronghold.installed)
        self.assertTrue(stronghold.uninstall(improvement.id))
        self.assertNotIn(improvement.id, stronghold.installed)

    def test_material_sources_and_role_position_affect_results(self):
        iron_blade = calculate_role_bonuses([("Iron Ore", "blade")])
        iron_plate = calculate_role_bonuses([("Iron Ore", "plate")])
        iron_lining = calculate_role_bonuses([("Iron Ore", "lining")])
        self.assertGreater(iron_blade["strength"], iron_plate["strength"])
        self.assertGreater(iron_plate["defense"], iron_blade["defense"])
        self.assertGreater(iron_lining["hp"], 0)
        from crafting import MATERIALS as crafting_materials
        self.assertIn("mine", crafting_materials["Iron Ore"]["sources"])
        self.assertIn("drop", crafting_materials["Dragon Scale"]["sources"])

    def test_component_recipe_consumes_multiple_materials(self):
        inventory = [
            create_item("Iron Ore"),
            create_item("Iron Ore"),
            create_item("Coal")
        ]
        requirements = recipe_catalog()["Steel Ingot"]
        self.assertTrue(has_materials(inventory, requirements))
        self.assertTrue(consume_materials(inventory, requirements))
        self.assertEqual(inventory, [])

    def test_blacksmith_level_tiers_scale_progressively(self):
        self.assertEqual(get_level_tier(1), 1)
        self.assertEqual(get_level_tier(10), 4)
        low = craft_weapon("Bronze Blade", "Sword", "Iron", 1)
        high = craft_weapon("Royal Blade", "Sword", "Dragon Scale", 10)
        self.assertGreater(high.character_level, low.character_level)
        self.assertGreater(high.crafting_tier, low.crafting_tier)
        self.assertGreater(high.strength_bonus, low.strength_bonus)

    def test_blacksmith_crafts_weapons_and_armor_for_all_slots(self):
        self.assertTrue(WEAPON_TEMPLATES)
        self.assertTrue(ARMOR_TEMPLATES)
        self.assertTrue(MATERIALS)
        weapon = craft_weapon("Stormfang", "Sword", "Storm Metal", 7)
        armor = craft_armor("Frost Guard", "Plate Armor", "Frost Crystal", 7)
        helm = craft_armor("Crown", "Light Armor", "Steel", 5, slot="helm")
        accessory = craft_armor("Ring", "Robes", "Mithril", 5, slot="accessory")
        self.assertEqual(weapon.slot, "weapon")
        self.assertEqual(weapon.element, "Lightning")
        self.assertEqual(armor.slot, "armor")
        self.assertGreater(armor.defense_bonus, 0)
        self.assertEqual(helm.slot, "helm")
        self.assertEqual(accessory.slot, "accessory")

    def test_base_templates_and_magic_tiers_are_available(self):
        self.assertIn("Fighter", BASE_CLASS_TEMPLATES)
        self.assertIn("Archmage", BASE_CLASS_TEMPLATES)
        self.assertEqual(get_spell_level_limit("none"), 0)
        self.assertEqual(get_spell_level_limit("low"), 1)
        self.assertEqual(get_spell_level_limit("medium"), 3)
        self.assertEqual(get_spell_level_limit("full"), 5)
        self.assertEqual(get_spell_slots("none", 10), {})
        self.assertEqual(set(get_spell_slots("medium", 3)), {1, 2, 3})

    def test_custom_spell_and_ability_registration(self):
        spell = register_spell(
            "Test Bolt",
            3,
            12,
            "Test damage spell.",
            "damage",
            spell_level=2
        )
        ability = register_ability(
            "Test Cleave",
            0,
            25,
            "Test skill.",
            "damage",
            unlock_level=3
        )
        self.assertEqual(spell.spell_level, 2)
        self.assertEqual(ability.name, "Test Cleave")

    def test_all_five_equipment_slots_exist_and_equip(self):
        fighter = Character("Mira", "Warrior", 60, 0, 10, 5)
        items = (
            create_item("Iron Sword"),
            create_item("Chain Mail"),
            create_item("Traveler's Helm"),
            create_item("Iron Ring"),
            create_item("Guardian Charm")
        )
        for item in items:
            self.assertTrue(fighter.equip(item))
        self.assertIsNotNone(fighter.weapon)
        self.assertIsNotNone(fighter.armor)
        self.assertIsNotNone(fighter.helm)
        self.assertIsNotNone(fighter.accessory_1)
        self.assertIsNotNone(fighter.accessory_2)

    def test_arena_is_reachable_from_the_expanded_world(self):
        with open(PROJECT_ROOT / "maps" / "world_map.json", encoding="utf-8") as file:
            world_map = json.load(file)

        arena_positions = [
            (x, y)
            for y, row in enumerate(world_map["tiles"])
            for x, tile in enumerate(row)
            if tile == "A"
        ]
        self.assertGreaterEqual(len(arena_positions), 1)
        self.assertTrue(
            any(value["map"] == "arena_map"
                for value in world_map["transitions"].values())
        )

    def test_arena_boss_is_a_scaled_special_version(self):
        challenge = load_arena_challenges()[0]
        boss = create_arena_boss(challenge)

        self.assertEqual(boss.name, "The Iron Champion")
        self.assertGreater(boss.max_hp, 100)
        self.assertEqual(boss.behavior, "heavy")

    def test_arena_requires_accepting_its_contract(self):
        from arena import run_arena

        with (
            patch("builtins.input", return_value="1"),
            patch("builtins.print") as print_mock
        ):
            run_arena(self.party)

        self.assertTrue(
            any(
                "castle quest board" in str(call).lower()
                for call in print_mock.call_args_list
            )
        )
        self.assertEqual(self.party.arena_wins, [])

    def test_winning_arena_bout_records_win_and_completes_trial(self):
        from arena import run_arena

        trial = Quest.from_definition(
            get_quest_definition("arena_iron_champion")
        )
        self.party.add_quest(trial)

        with (
            patch("arena.battle", return_value=True) as battle_mock,
            patch("builtins.input", return_value="1"),
            patch("builtins.print")
        ):
            run_arena(self.party)

        self.assertEqual(self.party.arena_wins, ["iron_champion"])
        self.assertTrue(trial.completed)
        self.assertIn("Paladin", self.party.unlocked_jobs)
        self.assertTrue(
            any(item.name == "Aegis of Dawn" for item in self.hero.inventory)
        )
        self.assertEqual(battle_mock.call_args.kwargs["enemies"][0].name, "The Iron Champion")

    def test_arena_win_contract_unlocks_job_and_legendary_gear(self):
        quest = Quest.from_definition(
            get_quest_definition("arena_iron_champion")
        )
        self.party.add_quest(quest)

        with patch("builtins.print"):
            self.party.update_quests(
                "arena_win",
                "The Iron Champion"
            )

        self.assertTrue(quest.completed)
        self.assertIn("Paladin", self.party.unlocked_jobs)
        self.assertTrue(
            any(item.name == "Aegis of Dawn" for item in self.hero.inventory)
        )

    def test_job_change_uses_unlocked_jobs_and_keeps_progression_stats(self):
        self.party.unlocked_jobs.add("Paladin")
        old_hp = self.hero.max_hp
        old_strength = self.hero.strength

        with (
            patch("town._choose_member", return_value=self.hero),
            patch("builtins.input", return_value="2"),
            patch("builtins.print")
        ):
            change_jobs(self.party)

        self.assertEqual(self.hero.job.name, "Paladin")
        self.assertEqual(self.hero.max_hp, old_hp)
        self.assertEqual(self.hero.strength, old_strength)
        self.assertGreaterEqual(self.hero.max_mp, 8)

    def test_equipping_and_replacing_legendary_gear_updates_stats(self):
        aegis = create_item("Aegis of Dawn")
        bow = create_item("Windrunner Bow")
        self.assertIsInstance(aegis, Equipment)
        self.assertIsInstance(bow, Equipment)
        self.hero.inventory.extend([aegis, bow])

        self.hero.equip(aegis)
        self.assertEqual(self.hero.defense, 13)
        self.assertEqual(self.hero.max_hp, 90)
        self.hero.equip(bow)
        self.assertEqual(self.hero.strength, 20)
        self.assertEqual(self.hero.defense, 13)

    def test_save_load_preserves_jobs_arena_wins_and_equipment(self):
        self.party.unlocked_jobs.add("Paladin")
        self.party.arena_wins.append("iron_champion")
        aegis = create_item("Aegis of Dawn")
        self.hero.inventory.append(aegis)
        self.hero.equip(aegis)
        expected = (
            self.hero.strength,
            self.hero.defense,
            self.hero.max_hp,
            self.hero.hp
        )
        previous_directory = os.getcwd()

        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with patch("builtins.print"):
                    save_game(self.party)
                    loaded = load_game()
            finally:
                os.chdir(previous_directory)

        restored = loaded.members[0]
        self.assertEqual(loaded.arena_wins, ["iron_champion"])
        self.assertIn("Paladin", loaded.unlocked_jobs)
        self.assertEqual(restored.armor.name, "Aegis of Dawn")
        self.assertEqual(
            (restored.strength, restored.defense, restored.max_hp, restored.hp),
            expected
        )


if __name__ == "__main__":
    unittest.main()
