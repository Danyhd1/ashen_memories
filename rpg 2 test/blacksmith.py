from dataclasses import dataclass

from items import Equipment, CRAFTED_ITEMS
from crafting import (
    MATERIALS as CRAFTING_MATERIALS,
    calculate_component_bonuses,
    calculate_role_bonuses,
)


WEAPON_TEMPLATES = {
    "Sword": {"slot": "weapon", "strength": 2, "max_hp": 0, "max_mp": 0, "element": "Neutral"},
    "Axe": {"slot": "weapon", "strength": 3, "max_hp": 0, "max_mp": 0, "element": "Neutral"},
    "Spear": {"slot": "weapon", "strength": 2, "max_hp": 2, "max_mp": 0, "element": "Neutral"},
    "Bow": {"slot": "weapon", "strength": 2, "max_hp": 0, "max_mp": 1, "element": "Neutral"},
    "Staff": {"slot": "weapon", "strength": 1, "max_hp": 0, "max_mp": 3, "element": "Neutral"},
    "Dagger": {"slot": "weapon", "strength": 2, "max_hp": 0, "max_mp": 0, "element": "Neutral"},
}

ARMOR_TEMPLATES = {
    "Light Armor": {"slot": "armor", "strength": 0, "defense": 2, "max_hp": 4},
    "Chain Armor": {"slot": "armor", "strength": 0, "defense": 4, "max_hp": 6},
    "Plate Armor": {"slot": "armor", "strength": 0, "defense": 6, "max_hp": 10},
    "Robes": {"slot": "armor", "strength": 0, "defense": 1, "max_hp": 2, "max_mp": 5},
}

CRAFT_SLOTS = ("weapon", "armor", "helm", "accessory")

MATERIALS = {
    name: {
        "cost": int(20 * rule["quality"]),
        "quality": rule["quality"],
        "element": rule["element"]
    }
    for name, rule in CRAFTING_MATERIALS.items()
}

# Backward-compatible common names used by older crafting files and saves.
MATERIALS["Iron"] = MATERIALS["Iron Ore"]
MATERIALS["Steel"] = MATERIALS["Steel Ingot"]
MATERIALS["Mithril"] = MATERIALS["Mithril Thread"]


@dataclass(frozen=True)
class CraftRecipe:
    name: str
    slot: str
    base_level: int
    base_cost: int
    strength: int
    defense: int
    max_hp: int
    max_mp: int
    element: str = "Neutral"


def get_level_tier(character_level):
    return max(1, min(10, (character_level - 1) // 3 + 1))


def validate_crafting(character, slot, character_level=None):
    level = character.level if character_level is None else character_level
    if slot not in CRAFT_SLOTS:
        raise ValueError(f"Unknown crafting slot: {slot}")
    if level < 1:
        raise ValueError("Crafting level must be at least 1.")
    return level


def craft_weapon(
    name,
    weapon_type,
    material,
    character_level=1,
    custom_suffix="",
    blade=None,
    core=None,
    binding=None
):
    if weapon_type not in WEAPON_TEMPLATES:
        raise ValueError(f"Unknown weapon type: {weapon_type}")
    if material not in MATERIALS:
        raise ValueError(f"Unknown material: {material}")

    tier = get_level_tier(character_level)
    template = WEAPON_TEMPLATES[weapon_type]
    material_rule = MATERIALS[material]
    quality = tier * material_rule["quality"]
    strength_bonus = max(1, int(template["strength"] + tier * 1.5 * material_rule["quality"]))
    max_hp_bonus = int(template["max_hp"] + tier)
    max_mp_bonus = int(template["max_mp"] + tier * 1.5)
    cost = int(material_rule["cost"] + 12 * tier + 8 * (tier * tier))
    full_name = f"{name}{' ' + custom_suffix if custom_suffix else ''}"
    description = (
        f"Level {character_level} {tier}-tier {material.lower()} {weapon_type.lower()}."
        f" Element: {material_rule['element']}."
    )
    item = Equipment(
        full_name,
        description,
        cost,
        "weapon",
        strength_bonus=strength_bonus,
        max_hp_bonus=max_hp_bonus,
        max_mp_bonus=max_mp_bonus
    )
    item.character_level = character_level
    item.crafting_tier = tier
    item.element = material_rule["element"]
    item.weapon_type = weapon_type
    item.material = material
    role_bonuses = calculate_role_bonuses([
        (blade or material, "blade"),
        (core or material, "core"),
        (binding, "binding"),
    ])
    item.strength_bonus += role_bonuses["strength"]
    item.defense_bonus += role_bonuses["defense"]
    item.max_hp_bonus += role_bonuses["hp"]
    item.max_mp_bonus += role_bonuses["mp"]
    item.crafting_components = {
        "blade": blade or material,
        "core": core or material,
        "binding": binding
    }
    CRAFTED_ITEMS[full_name] = item
    return item


def craft_armor(
    name,
    armor_type,
    material,
    character_level=1,
    slot="armor",
    plate=None,
    lining=None,
    enchantment=None
):
    if armor_type not in ARMOR_TEMPLATES:
        raise ValueError(f"Unknown armor type: {armor_type}")
    if material not in MATERIALS:
        raise ValueError(f"Unknown material: {material}")

    tier = get_level_tier(character_level)
    template = ARMOR_TEMPLATES[armor_type]
    material_rule = MATERIALS[material]
    quality = tier * material_rule["quality"]
    defense_bonus = max(1, int(template["defense"] + tier * 1.25 * material_rule["quality"]))
    max_hp_bonus = int(template.get("max_hp", 0) + tier * 2)
    max_mp_bonus = int(template.get("max_mp", 0) + tier)
    cost = int(material_rule["cost"] + 10 * tier + 7 * (tier * tier))
    item = Equipment(
        name,
        f"Level {character_level} {tier}-tier {material.lower()} {armor_type.lower()}.",
        cost,
        slot,
        defense_bonus=defense_bonus,
        max_hp_bonus=max_hp_bonus,
        max_mp_bonus=max_mp_bonus
    )
    item.character_level = character_level
    item.crafting_tier = tier
    item.element = material_rule["element"]
    item.armor_type = armor_type
    item.material = material
    role_bonuses = calculate_role_bonuses([
        (plate or material, "plate"),
        (lining, "lining"),
        (enchantment, "enchantment"),
    ])
    item.strength_bonus += role_bonuses["strength"]
    item.defense_bonus += role_bonuses["defense"]
    item.max_hp_bonus += role_bonuses["hp"]
    item.max_mp_bonus += role_bonuses["mp"]
    item.crafting_components = {
        "plate": plate or material,
        "lining": lining,
        "enchantment": enchantment
    }
    CRAFTED_ITEMS[name] = item
    return item


def craft_item(name, slot, base_type, material, character_level=1, custom_suffix=""):
    level = validate_crafting(type("CraftTarget", (), {"level": character_level})(), slot, character_level)
    if slot == "weapon":
        return craft_weapon(name, base_type, material, level, custom_suffix)
    if slot == "armor":
        return craft_armor(name, base_type, material, level)
    raise ValueError(f"No custom crafter is available for slot: {slot}")


def blacksmith_menu(party):
    if not party.members:
        print("No character is available to receive crafted equipment.")
        return

    leader = party.members[0]
    print("\n===== THE BLACKSMITH =====")
    print("1. Craft weapon")
    print("2. Craft armor")
    print("3. View crafting levels")
    print("0. Leave")

    choice = input("> ").strip()
    if choice == "1":
        weapon_types = list(WEAPON_TEMPLATES)
        print("Choose weapon type:")
        for index, weapon_type in enumerate(weapon_types, 1):
            print(f"{index}. {weapon_type}")
        try:
            selected = weapon_types[int(input("> ")) - 1]
        except (ValueError, IndexError):
            print("Invalid weapon choice.")
            return
        print("Choose material:")
        materials = list(MATERIALS)
        for index, material in enumerate(materials, 1):
            print(f"{index}. {material}")
        try:
            material = materials[int(input("> ")) - 1]
        except (ValueError, IndexError):
            print("Invalid material choice.")
            return
        name = input("Weapon name: ").strip() or f"{material} {selected}"
        item = craft_weapon(name, selected, material, leader.level)
        if leader.gold < item.value:
            print(f"Not enough gold. Crafting costs {item.value} gold.")
            return
        leader.gold -= item.value
        leader.inventory.append(item)
        print(f"{item.name} was forged for {item.value} gold.")
    elif choice == "2":
        armor_types = list(ARMOR_TEMPLATES)
        print("Choose armor type:")
        for index, armor_type in enumerate(armor_types, 1):
            print(f"{index}. {armor_type}")
        try:
            selected = armor_types[int(input("> ")) - 1]
        except (ValueError, IndexError):
            print("Invalid armor choice.")
            return
        materials = list(MATERIALS)
        print("Choose material:")
        for index, material in enumerate(materials, 1):
            print(f"{index}. {material}")
        try:
            material = materials[int(input("> ")) - 1]
        except (ValueError, IndexError):
            print("Invalid material choice.")
            return
        name = input("Armor name: ").strip() or f"{material} {selected}"
        item = craft_armor(name, selected, material, leader.level)
        if leader.gold < item.value:
            print(f"Not enough gold. Crafting costs {item.value} gold.")
            return
        leader.gold -= item.value
        leader.inventory.append(item)
        print(f"{item.name} was forged for {item.value} gold.")
    elif choice == "3":
        for member in party.members:
            print(
                f"{member.name}: level {member.level}, "
                f"craft tier {get_level_tier(member.level)}"
            )
