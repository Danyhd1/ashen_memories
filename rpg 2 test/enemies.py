import json
from pathlib import Path


class Enemy:

    def __init__(
        self,
        name,
        max_hp,
        strength,
        defense,
        exp_reward,
        gold_reward,
        behavior="basic",
        drops=None,
        enemy_type="Beast",
        element="Neutral"
    ):

        self.name = name

        self.max_hp = max_hp
        self.hp = max_hp

        self.strength = strength
        self.defense = defense

        self.exp_reward = exp_reward
        self.gold_reward = gold_reward
        self.behavior = behavior
        self.drops = drops or []
        self.enemy_type = enemy_type
        self.element = element
        self.status_effects = {}
        self.defending = False

    def is_alive(self):

        return self.hp > 0

    def take_damage(
        self,
        amount
    ):

        self.hp -= amount

        if self.hp < 0:

            self.hp = 0

    def apply_status(self, status, duration):
        if status and duration > 0:
            self.status_effects[status] = max(
                duration,
                self.status_effects.get(status, 0)
            )

    def has_status(self, status):
        return self.status_effects.get(status, 0) > 0


def get_enemy_file_path():

    base_folder = Path(
        __file__
    ).parent

    return (
        base_folder
        / "data"
        / "enemies.json"
    )


def load_enemy_data():

    enemy_file_path = (
        get_enemy_file_path()
    )

    with open(
        enemy_file_path,
        "r"
    ) as file:

        return json.load(
            file
        )


ENEMY_TYPES = (
    ("Goblin", "Beast", "Neutral"),
    ("Wolf", "Beast", "Neutral"),
    ("Snake", "Beast", "Poison"),
    ("Skeleton", "Undead", "Shadow"),
    ("Zombie", "Undead", "Poison"),
    ("Ogre", "Humanoid", "Earth"),
    ("Harpy", "Avian", "Wind"),
    ("Bandit", "Humanoid", "Neutral"),
    ("Slime", "Nature", "Water"),
    ("Shaman", "Humanoid", "Shadow"),
    ("Wraith", "Undead", "Shadow"),
    ("Wyvern", "Dragon", "Fire"),
    ("Dark Knight", "Undead", "Shadow"),
    ("Dread Captain", "Humanoid", "Neutral"),
    ("Orc", "Humanoid", "Earth"),
    ("Treant", "Nature", "Nature"),
    ("Mimic", "Construct", "Neutral"),
    ("Basilisk", "Beast", "Poison"),
    ("Golem", "Construct", "Earth"),
    ("Ice Wyrm", "Dragon", "Ice"),
    ("Thunder Hawk", "Avian", "Lightning"),
    ("Fire Imp", "Fiend", "Fire"),
    ("Tide Witch", "Humanoid", "Water"),
    ("Stone Tortoise", "Beast", "Earth"),
    ("Cloud Elemental", "Elemental", "Wind"),
    ("Storm Elemental", "Elemental", "Lightning"),
    ("Cinder Elemental", "Elemental", "Fire"),
    ("Frost Elemental", "Elemental", "Ice"),
    ("Void Stalker", "Fiend", "Shadow"),
    ("Sun Priest", "Humanoid", "Light"),
    ("Cave Bat", "Beast", "Shadow"),
    ("Lava Crab", "Beast", "Fire"),
    ("Dune Scorpion", "Beast", "Poison"),
    ("War Automaton", "Construct", "Neutral"),
    ("Crystal Dragon", "Dragon", "Light"),
    ("Abyssal Leviathan", "Dragon", "Water"),
)

ENEMY_VARIATION_COUNT = 10


def get_enemy_catalog():
    return [
        {
            "name": type_name,
            "enemy_type": enemy_type,
            "element": element,
            "variations": [
                f"{type_name} {tier}"
                for tier in range(1, ENEMY_VARIATION_COUNT + 1)
            ]
        }
        for type_name, enemy_type, element in ENEMY_TYPES
    ]


def generate_enemy_variation(base_name, tier):
    base = load_enemy_data().get(base_name)
    if base is None:
        base = {
            "max_hp": 30,
            "strength": 7,
            "defense": 4,
            "exp_reward": 20,
            "gold_reward": 12,
            "behavior": "basic",
            "drops": []
        }
    scale = 0.75 + (tier * 0.22)
    return {
        "max_hp": max(1, int(base["max_hp"] * scale)),
        "strength": max(1, int(base["strength"] * scale)),
        "defense": max(0, int(base["defense"] * scale)),
        "exp_reward": max(1, int(base["exp_reward"] * scale)),
        "gold_reward": max(1, int(base["gold_reward"] * scale)),
        "behavior": base.get("behavior", "basic"),
        "drops": base.get("drops", [])
    }


def create_enemy(
    enemy_name
):

    enemy_data = (
        load_enemy_data()
    )

    base_name = enemy_name
    variation = None
    if enemy_name not in enemy_data:
        for type_name, enemy_type, element in ENEMY_TYPES:
            if enemy_name.startswith(type_name + " "):
                base_name = type_name
                suffix = enemy_name.removeprefix(type_name + " ").strip()
                if suffix.isdigit():
                    variation = int(suffix)
                break

    if enemy_name not in enemy_data and variation is not None:
        enemy_data = dict(enemy_data)
        enemy_data[enemy_name] = generate_enemy_variation(
            base_name,
            max(1, min(10, variation))
        )
        data = enemy_data[enemy_name]
        for type_name, enemy_type, element in ENEMY_TYPES:
            if base_name == type_name:
                data["enemy_type"] = enemy_type
                data["element"] = element
                break
    elif enemy_name not in enemy_data:

        print(
            f"Enemy not found: "
            f"{enemy_name}"
        )

        return None

    data = enemy_data[
        enemy_name
    ]

    return Enemy(

        enemy_name,

        data["max_hp"],

        data["strength"],

        data["defense"],

        data["exp_reward"],
        data["gold_reward"],
        data.get("behavior", "basic"),
        data.get("drops", []),
        data.get("enemy_type", "Beast"),
        data.get("element", "Neutral")

    )