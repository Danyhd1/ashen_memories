import unittest
from unittest.mock import patch

import battle
from elements import ELEMENTS, element_multiplier
from enemies import ENEMY_TYPES, ENEMY_VARIATION_COUNT, get_enemy_catalog, create_enemy
from skills import (
    SKILL_POINT_RULES,
    SKILL_REGISTRY,
    can_learn_skill,
    learn_skill,
    get_skill_points_per_level,
    get_skill_power,
    create_skill_tree,
)
from characters import Character
from enemies import Enemy, create_enemy
from magic import create_spell, get_combat_abilities
from party import Party


class BattleSystemTests(unittest.TestCase):

    def setUp(self):
        self.party = Party()
        self.warrior = Character("Rin", "Warrior", 60, 0, 10, 5)
        self.party.add_member(self.warrior)

    def test_skill_points_follow_magic_tier_rules(self):
        self.assertEqual(get_skill_points_per_level("none"), 6)
        self.assertEqual(get_skill_points_per_level("low"), 4)
        self.assertEqual(get_skill_points_per_level("medium"), 3)
        self.assertEqual(get_skill_points_per_level("full"), 2)
        self.assertEqual(SKILL_POINT_RULES["full"], 2)

    def test_skill_learning_requires_level_points_and_prerequisites(self):
        quick = SKILL_REGISTRY["quick_strike"]
        mastery = SKILL_REGISTRY["battle_mastery"]
        self.warrior.skill_points = 3
        self.assertTrue(can_learn_skill(self.warrior, quick))
        learned = learn_skill(self.warrior, quick.id)
        self.assertEqual(learned.name, "Quick Strike")
        self.assertEqual(self.warrior.skill_points, 2)
        self.assertFalse(can_learn_skill(self.warrior, mastery))

    def test_skill_power_scales_with_character_level(self):
        skill = SKILL_REGISTRY["precision"]
        self.assertGreater(
            get_skill_power(skill, 8),
            get_skill_power(skill, 4)
        )

    def test_custom_skill_tree_supports_prerequisites(self):
        create_skill_tree(
            "Test Tree",
            {
                "id": "test_root",
                "name": "Test Root",
                "unlock_level": 1,
                "cost": 1,
                "base_power": 12,
            },
            [
                {
                    "id": "test_branch",
                    "name": "Test Branch",
                    "unlock_level": 3,
                    "cost": 2,
                    "prerequisites": ["test_root"],
                    "base_power": 20,
                }
            ]
        )
        root = SKILL_REGISTRY["test_root"]
        branch = SKILL_REGISTRY["test_branch"]
        self.assertEqual(root.category, "Test Tree")
        self.assertIn("test_root", branch.prerequisites)

    def test_enemy_catalog_has_36_types_and_10_variations(self):
        catalog = get_enemy_catalog()
        self.assertEqual(len(ENEMY_TYPES), 36)
        self.assertEqual(len(catalog), 36)
        self.assertEqual(ENEMY_VARIATION_COUNT, 10)
        for entry in catalog:
            self.assertEqual(len(entry["variations"]), 10)

    def test_enemy_variations_scale_from_weak_to_strong(self):
        weak = create_enemy("Goblin 1")
        strong = create_enemy("Goblin 10")
        self.assertGreater(strong.max_hp, weak.max_hp)
        self.assertGreater(strong.strength, weak.strength)
        self.assertEqual(weak.enemy_type, "Beast")

    def test_elements_apply_weakness_and_resistance(self):
        self.assertIn("Fire", ELEMENTS)
        self.assertEqual(element_multiplier("Fire", "Ice", "Beast"), 1.5)
        self.assertEqual(element_multiplier("Fire", "Fire", "Beast"), 0.5)
        self.assertEqual(element_multiplier("Neutral", "Neutral", "Beast"), 1.0)

    def test_warrior_skills_work_without_mp(self):
        skills = get_combat_abilities(self.warrior)
        power_strike = next(skill for skill in skills if skill.name == "Power Strike")
        enemy = Enemy("Test", 40, 5, 0, 1, 1)

        with (
            patch("magic.random.randint", return_value=power_strike.power),
            patch("builtins.print")
        ):
            self.assertTrue(power_strike.cast(self.warrior, enemy))

        self.assertEqual(self.warrior.mp, 0)
        self.assertEqual(enemy.hp, 10)

    def test_poison_damages_at_round_start(self):
        enemy = Enemy("Test", 24, 5, 0, 1, 1)
        enemy.apply_status("poison", 2)

        with patch("builtins.print"):
            battle.apply_round_effects([enemy])

        self.assertEqual(enemy.hp, 22)

    def test_defending_reduces_incoming_damage(self):
        attacker = Enemy("Test", 10, 10, 0, 1, 1)
        self.warrior.defending = True

        with patch("builtins.print"):
            damage = battle.attack(attacker, self.warrior)

        self.assertEqual(damage, 2)
        self.assertEqual(self.warrior.hp, 58)

    def test_multi_target_spell_spends_mp_once(self):
        mage = Character("Ash", "Black Mage", 35, 25, 3, 1)
        self.party.members[0] = mage
        first = Enemy("First", 100, 1, 0, 1, 1)
        second = Enemy("Second", 100, 1, 0, 1, 1)
        enemies = [first, second]

        with (
            patch("battle.choose_ability", return_value=create_spell("Firestorm")),
            patch("battle.random.randint", return_value=18),
            patch("builtins.print")
        ):
            self.assertTrue(battle.handle_ability(mage, self.party, enemies))

        self.assertEqual(mage.mp, 13)
        self.assertEqual(first.hp, 82)
        self.assertEqual(second.hp, 82)

    def test_smoke_bomb_improves_escape_chance(self):
        self.warrior.apply_status("escape_boost", 2)

        with (
            patch("battle.random.randint", return_value=80),
            patch("builtins.print")
        ):
            self.assertTrue(battle.attempt_run(self.party))

    def test_enemy_data_includes_new_behavior_types(self):
        self.assertEqual(create_enemy("Shaman").behavior, "support")
        self.assertEqual(create_enemy("Wyvern").behavior, "heavy")
        self.assertIsNotNone(create_spell("Firestorm"))

    def test_battle_awards_rewards_after_victory(self):
        enemy = Enemy("Goblin", 1, 1, 0, 10, 5)
        self.warrior.strength = 10

        with (
            patch("battle.create_enemy_group", return_value=[enemy]),
            patch("builtins.input", side_effect=["1", "1"]),
            patch("builtins.print")
        ):
            result = battle.battle(self.party, "Grassland")

        self.assertTrue(result)
        self.assertEqual(self.warrior.exp, 10)
        self.assertEqual(self.warrior.gold, 105)


if __name__ == "__main__":
    unittest.main()
