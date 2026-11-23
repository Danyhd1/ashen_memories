import json
from pathlib import Path

from battle import battle
from enemies import create_enemy


ARENA_DATA_PATH = Path(__file__).parent / "data" / "arena.json"


def load_arena_challenges():
    with open(ARENA_DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def create_arena_boss(challenge):
    enemy = create_enemy(challenge["base_enemy"])
    if enemy is None:
        raise ValueError(
            f"Arena challenge references unknown enemy '{challenge['base_enemy']}'."
        )

    enemy.name = challenge["name"]
    enemy.max_hp = challenge["max_hp"]
    enemy.hp = challenge["max_hp"]
    enemy.strength = challenge["strength"]
    enemy.defense = challenge["defense"]
    enemy.exp_reward = challenge["exp_reward"]
    enemy.gold_reward = challenge["gold_reward"]
    enemy.behavior = challenge.get("behavior", enemy.behavior)
    enemy.drops = challenge.get("drops", [])
    return enemy


def run_arena(party):
    challenges = load_arena_challenges()
    next_index = len(party.arena_wins)

    print("\n===== THE CHAMPIONS' ARENA =====")
    if next_index >= len(challenges):
        print("The arena has no further champions to challenge.")
        print("Your party has completed the championship circuit.")
        return

    challenge = challenges[next_index]
    quest_id = f"arena_{challenge['id']}"
    accepted_quest = next(
        (
            quest for quest in party.quests
            if quest.quest_id == quest_id and not quest.completed
        ),
        None
    )
    if accepted_quest is None:
        print(
            "\nThe arena steward asks you to accept the matching trial "
            "contract from the castle quest board first."
        )
        return

    print(f"Next bout: {challenge['name']}")
    print(challenge["description"])
    print(
        f"Champion: {challenge['name']} "
        f"({challenge['base_enemy']} lineage)"
    )
    print("1. Enter the bout")
    print("0. Return")

    choice = input("> ").strip()
    if choice == "0":
        return
    if choice != "1":
        print("Invalid choice.")
        return

    print(f"\nThe arena doors open. Face {challenge['name']}!")
    boss = create_arena_boss(challenge)
    victory = battle(party, "Arena", enemies=[boss])

    if victory:
        party.arena_wins.append(challenge["id"])
        party.update_quests("arena_win", challenge["name"])
        print(f"\nArena victory recorded: {challenge['name']}.")
