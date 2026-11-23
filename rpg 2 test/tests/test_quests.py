import os
import tempfile
import unittest
from unittest.mock import patch

from characters import Character
from enemies import Enemy
from items import create_item
from party import Party
from quests import Quest, available_quests, get_quest_definition
from save import load_game, save_game


class QuestLineTests(unittest.TestCase):

    def setUp(self):
        self.party = Party()
        self.hero = Character("Mira", "Warrior", 60, 0, 10, 5)
        self.party.add_member(self.hero)
        self.party.add_quest(
            Quest.from_definition(get_quest_definition("first_contract"))
        )

    def test_kill_objective_awards_rewards_and_unlocks_fetch_contract(self):
        with patch("builtins.print"):
            self.party.update_quests("kill", "Goblin", quantity=3)

        first = self.party.quests[0]
        self.assertTrue(first.completed)
        self.assertEqual(self.hero.gold, 140)
        self.assertEqual(self.hero.exp, 15)
        self.assertIn(
            "alchemist_order",
            {quest["id"] for quest in available_quests(self.party)}
        )

    def test_fetch_quest_tracks_material_and_adds_it_to_inventory(self):
        self.party.quests.append(
            Quest.from_definition(get_quest_definition("alchemist_order"))
        )

        with patch("builtins.print"):
            self.party.update_quests("collect", "Slime Gel", quantity=2)

        fetch_quest = self.party.quests[1]
        self.assertEqual(fetch_quest.progress, 2)
        self.assertEqual(
            [item.name for item in self.hero.inventory],
            ["Slime Gel", "Slime Gel"]
        )

    def test_bounty_counts_kills_and_only_rewards_once(self):
        bounty = Quest.from_definition(
            get_quest_definition("red_knives_bounty")
        )
        self.party.add_quest(bounty)

        with patch("builtins.print"):
            self.party.update_quests("kill", "Bandit", quantity=3)
            self.party.update_quests("kill", "Bandit")

        self.assertTrue(bounty.completed)
        self.assertEqual(bounty.progress, 3)
        self.assertEqual(self.hero.gold, 200)

    def test_escort_requires_visiting_exact_destination(self):
        escort = Quest.from_definition(get_quest_definition("lost_courier"))
        self.party.add_quest(escort)

        with patch("builtins.print"):
            self.party.update_quests(
                "visit",
                "town_map",
                metadata={"x": 1, "y": 1}
            )
            self.party.update_quests(
                "visit",
                "town_map",
                metadata={"x": 2, "y": 1}
            )

        self.assertTrue(escort.completed)
        self.assertEqual(escort.progress, 1)

    def test_completed_kill_bounty_unlocks_boss_contract(self):
        self.party.quests.append(
            Quest.from_definition(get_quest_definition("alchemist_order"))
        )
        self.party.quests.append(
            Quest.from_definition(get_quest_definition("red_knives_bounty"))
        )
        self.party.quests.append(
            Quest.from_definition(get_quest_definition("lost_courier"))
        )
        self.party.quests[-1].completed = True

        self.assertIn(
            "dread_captain",
            {quest["id"] for quest in available_quests(self.party)}
        )

    def test_quest_state_serializes_all_campaign_details(self):
        quest = Quest.from_definition(get_quest_definition("lost_courier"))
        quest.progress = 1
        restored = Quest(**{
            "name": quest.name,
            "objective_type": quest.objective_type,
            "target": quest.target,
            "goal": quest.goal,
            "quest_id": quest.quest_id,
            "description": quest.description,
            "prerequisites": quest.prerequisites,
            "reward_gold": quest.reward_gold,
            "reward_exp": quest.reward_exp,
            "reward_items": quest.reward_items,
            "reward_jobs": quest.reward_jobs,
            "destination": quest.destination,
            "progress": quest.progress,
            "completed": quest.completed
        })

        self.assertEqual(restored.to_dict(), quest.to_dict())

    def test_save_load_preserves_questline_and_fetch_inventory(self):
        self.party.quests[0].progress = 2
        self.party.members[0].inventory.append(create_item("Slime Gel"))
        previous_directory = os.getcwd()

        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with patch("builtins.print"):
                    save_game(self.party)
                    loaded = load_game()
            finally:
                os.chdir(previous_directory)

        self.assertEqual(loaded.quests[0].quest_id, "first_contract")
        self.assertEqual(loaded.quests[0].progress, 2)
        self.assertEqual(loaded.quests[0].reward_gold, 40)
        self.assertEqual(loaded.members[0].inventory[0].name, "Slime Gel")

    def test_enemy_drop_metadata_is_available_for_fetches(self):
        slime = Enemy("Slime", 30, 4, 2, 10, 5, drops=[
            {"item": "Slime Gel", "chance": 1.0}
        ])
        self.assertEqual(slime.drops[0]["item"], "Slime Gel")


if __name__ == "__main__":
    unittest.main()
