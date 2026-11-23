import json
import os
from items import Equipment

from characters import Character
from items import create_item
from magic import create_spell
from party import Party
from quests import Quest
from stronghold import Stronghold


def save_game(party, path="save.json"):

    data = {
        "members": [],
        "quests": [],
        "discovered_events": list(party.discovered_events),
        "unlocked_jobs": sorted(party.unlocked_jobs),
        "arena_wins": list(party.arena_wins),
        "stronghold": party.stronghold.to_dict()
    }

    for member in party.members:

        equipped_items = [
            item for item in (
                member.weapon,
                member.armor,
                getattr(member, "helm", None),
                getattr(member, "accessory_1", None),
                getattr(member, "accessory_2", None)
            )
            if item is not None
        ]
        strength_bonus = sum(item.strength_bonus for item in equipped_items)
        defense_bonus = sum(item.defense_bonus for item in equipped_items)
        max_hp_bonus = sum(item.max_hp_bonus for item in equipped_items)
        max_mp_bonus = sum(item.max_mp_bonus for item in equipped_items)

        character_data = {
            "name": member.name,
            "job": member.job.name,
            "level": member.level,
            "exp": member.exp,
            "max_hp": member.max_hp - max_hp_bonus,
            "hp": member.hp,
            "max_mp": member.max_mp - max_mp_bonus,
            "mp": member.mp,
            "strength": member.strength - strength_bonus,
            "defense": member.defense - defense_bonus,
            "gold": member.gold,
            "race": member.race,
            "custom_job": getattr(member, "custom_job_name", None),
            "magic_type": getattr(member, "magic_type", "none"),
            "template": getattr(member, "template", None),
            "skill_points": getattr(member, "skill_points", 0),
            "learned_skills": getattr(member, "learned_skills", []),
            "base_max_hp": getattr(member, "base_max_hp", member.max_hp),
            "base_max_mp": getattr(member, "base_max_mp", member.max_mp),
            "base_strength": getattr(member, "base_strength", member.strength),
            "base_defense": getattr(member, "base_defense", member.defense),
            "inventory": [item.name for item in member.inventory],
            "crafted_inventory": [
                {
                    "name": item.name,
                    "description": item.description,
                    "value": item.value,
                    "slot": item.slot,
                    "strength_bonus": item.strength_bonus,
                    "defense_bonus": item.defense_bonus,
                    "max_hp_bonus": item.max_hp_bonus,
                    "max_mp_bonus": item.max_mp_bonus,
                    "character_level": getattr(item, "character_level", member.level),
                    "crafting_tier": getattr(item, "crafting_tier", 1),
                    "element": getattr(item, "element", "Neutral"),
                    "weapon_type": getattr(item, "weapon_type", ""),
                    "armor_type": getattr(item, "armor_type", ""),
                    "material": getattr(item, "material", "")
                }
                for item in member.inventory
                if isinstance(item, Equipment)
                and getattr(item, "material", "") != ""
            ],
            "spells": [spell.name for spell in member.spells],
            "equipped_weapon": member.weapon.name if member.weapon else None,
            "equipped_armor": member.armor.name if member.armor else None,
            "equipped_helm": getattr(member, "helm", None).name if getattr(member, "helm", None) else None,
            "equipped_accessory_1": getattr(member, "accessory_1", None).name if getattr(member, "accessory_1", None) else None,
            "equipped_accessory_2": getattr(member, "accessory_2", None).name if getattr(member, "accessory_2", None) else None
        }

        data["members"].append(character_data)

    for quest in party.quests:
        data["quests"].append(quest.to_dict())

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print("\nGame saved.")


def load_game(path="save.json", prompt_on_corrupt=True):

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("\nNo save file found.")
        return None
    except json.JSONDecodeError:
        print("\nSave file is corrupted.")
        if not prompt_on_corrupt:
            return None

        choice = input("Delete corrupted save? (y/n): ").lower()
        if choice == "y":
            try:
                os.remove(path)
                print("Save file deleted.")
            except OSError:
                print("Unable to delete save file.")

        return None

    party = Party()
    party.discovered_events = data.get("discovered_events", [])
    party.unlocked_jobs.update(data.get("unlocked_jobs", []))
    party.arena_wins = data.get("arena_wins", [])
    party.stronghold = Stronghold.from_dict(data.get("stronghold", {}))

    for member_data in data.get("members", []):
        character = Character(
            member_data["name"],
            member_data["job"],
            member_data.get("base_max_hp", member_data["max_hp"]),
            member_data.get("base_max_mp", member_data["max_mp"]),
            member_data.get("base_strength", member_data["strength"]),
            member_data.get("base_defense", member_data["defense"]),
            race=member_data.get("race", "Human"),
            custom_job=member_data.get("custom_job"),
            abilities=member_data.get("spells", []),
            magic_type=member_data.get("magic_type", "none"),
            template=member_data.get("template")
        )

        character.level = member_data.get("level", 1)
        character.skill_points = member_data.get("skill_points", 0)
        character.learned_skills = list(member_data.get("learned_skills", []))
        character.exp = member_data.get("exp", 0)
        character.hp = member_data.get("hp", character.max_hp)
        character.mp = member_data.get("mp", character.max_mp)
        character.gold = member_data.get("gold", 100)

        for item_name in member_data.get("inventory", []):
            item = create_item(item_name)
            if item is not None:
                character.inventory.append(item)

        normal_inventory_names = set(member_data.get("inventory", []))
        if member_data.get("crafted_inventory"):
            character.inventory = [
                item for item in character.inventory
                if not (
                    hasattr(item, "slot")
                    and getattr(item, "material", "") == ""
                    and item.name not in normal_inventory_names
                )
            ]
            for crafted in member_data["crafted_inventory"]:
                item = Equipment(
                    crafted["name"],
                    crafted["description"],
                    crafted["value"],
                    crafted["slot"],
                    crafted.get("strength_bonus", 0),
                    crafted.get("defense_bonus", 0),
                    crafted.get("max_hp_bonus", 0),
                    crafted.get("max_mp_bonus", 0)
                )
                for field in (
                    "character_level",
                    "crafting_tier",
                    "element",
                    "weapon_type",
                    "armor_type",
                    "material"
                ):
                    setattr(item, field, crafted.get(field))
                if not any(existing.name == item.name for existing in character.inventory):
                    character.inventory.append(item)

        for spell_name in member_data.get("spells", []):
            spell = create_spell(spell_name)
            if spell is not None:
                character.spells.append(spell)

        for slot in (
            "weapon",
            "armor",
            "helm",
            "accessory_1",
            "accessory_2"
        ):
            equipped_name = member_data.get(f"equipped_{slot}")
            if equipped_name:
                equipment = next(
                    (
                        item for item in character.inventory
                        if item.name == equipped_name
                    ),
                    None
                )
                if equipment is not None:
                    character.equip(equipment)

        party.add_member(character)

    for quest_data in data.get("quests", []):
        quest = Quest(
            quest_data["name"],
            quest_data.get("objective_type", "kill"),
            quest_data.get("target", ""),
            quest_data.get("goal", 1),
            quest_id=quest_data.get("id", quest_data["name"]),
            description=quest_data.get("description", ""),
            prerequisites=quest_data.get("prerequisites", []),
            reward_gold=quest_data.get("reward_gold", 0),
            reward_exp=quest_data.get("reward_exp", 0),
            reward_items=quest_data.get("reward_items", []),
            reward_jobs=quest_data.get("reward_jobs", []),
            destination=quest_data.get("destination"),
            progress=quest_data.get("progress", 0),
            completed=quest_data.get("completed", False)
        )
        party.add_quest(quest)

    print("\nGame loaded.")
    return party