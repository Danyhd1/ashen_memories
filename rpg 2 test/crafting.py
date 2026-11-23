import random


MATERIALS = {
    "Iron Ore": {
        "sources": ["mine", "shop"],
        "quality": 1.0,
        "element": "Neutral",
        "roles": {
            "blade": {"strength": 3, "defense": 0, "hp": 0, "mp": 0},
            "core": {"strength": 1, "defense": 2, "hp": 3, "mp": 0},
            "plate": {"strength": 0, "defense": 3, "hp": 4, "mp": 0},
            "binding": {"strength": 1, "defense": 1, "hp": 1, "mp": 0},
            "lining": {"strength": 0, "defense": 1, "hp": 3, "mp": 0},
            "enchantment": {"strength": 1, "defense": 0, "hp": 0, "mp": 1},
        },
    },
    "Steel Ingot": {
        "sources": ["craft", "shop"],
        "quality": 1.35,
        "element": "Neutral",
        "ingredients": {"Iron Ore": 2, "Coal": 1},
        "roles": {
            "blade": {"strength": 5, "defense": 0, "hp": 0, "mp": 0},
            "core": {"strength": 2, "defense": 4, "hp": 5, "mp": 0},
            "plate": {"strength": 0, "defense": 5, "hp": 7, "mp": 0},
            "binding": {"strength": 2, "defense": 2, "hp": 2, "mp": 0},
            "lining": {"strength": 0, "defense": 2, "hp": 5, "mp": 1},
            "enchantment": {"strength": 2, "defense": 0, "hp": 0, "mp": 2},
        },
    },
    "Mithril Thread": {
        "sources": ["mine", "drop"],
        "quality": 1.8,
        "element": "Light",
        "roles": {
            "blade": {"strength": 4, "defense": 1, "hp": 0, "mp": 4},
            "core": {"strength": 2, "defense": 3, "hp": 4, "mp": 6},
            "plate": {"strength": 0, "defense": 4, "hp": 8, "mp": 5},
            "binding": {"strength": 2, "defense": 2, "hp": 2, "mp": 4},
            "lining": {"strength": 0, "defense": 3, "hp": 6, "mp": 8},
            "enchantment": {"strength": 2, "defense": 1, "hp": 2, "mp": 10},
        },
    },
    "Dragon Scale": {
        "sources": ["drop"],
        "quality": 2.2,
        "element": "Fire",
        "roles": {
            "blade": {"strength": 9, "defense": 1, "hp": 2, "mp": 0},
            "core": {"strength": 5, "defense": 5, "hp": 8, "mp": 0},
            "plate": {"strength": 2, "defense": 9, "hp": 12, "mp": 0},
            "binding": {"strength": 4, "defense": 3, "hp": 5, "mp": 0},
            "lining": {"strength": 1, "defense": 4, "hp": 10, "mp": 2},
            "enchantment": {"strength": 5, "defense": 1, "hp": 3, "mp": 4},
        },
    },
    "Frost Crystal": {
        "sources": ["mine", "drop"],
        "quality": 1.95,
        "element": "Ice",
        "roles": {
            "blade": {"strength": 6, "defense": 0, "hp": 0, "mp": 5},
            "core": {"strength": 3, "defense": 4, "hp": 4, "mp": 7},
            "plate": {"strength": 0, "defense": 7, "hp": 8, "mp": 6},
            "binding": {"strength": 2, "defense": 3, "hp": 3, "mp": 5},
            "lining": {"strength": 0, "defense": 3, "hp": 5, "mp": 10},
            "enchantment": {"strength": 3, "defense": 1, "hp": 2, "mp": 12},
        },
    },
    "Storm Metal": {
        "sources": ["mine", "craft"],
        "quality": 2.05,
        "element": "Lightning",
        "ingredients": {"Iron Ore": 3, "Thunder Quartz": 1},
        "roles": {
            "blade": {"strength": 8, "defense": 0, "hp": 0, "mp": 3},
            "core": {"strength": 4, "defense": 5, "hp": 5, "mp": 5},
            "plate": {"strength": 1, "defense": 8, "hp": 9, "mp": 4},
            "binding": {"strength": 3, "defense": 3, "hp": 3, "mp": 4},
            "lining": {"strength": 1, "defense": 4, "hp": 6, "mp": 8},
            "enchantment": {"strength": 4, "defense": 1, "hp": 2, "mp": 9},
        },
    },
    "Coal": {
        "sources": ["mine", "wild"],
        "quality": 0.8,
        "element": "Fire",
        "roles": {"binding": {"strength": 0, "defense": 1, "hp": 0, "mp": 0}},
    },
    "Thunder Quartz": {
        "sources": ["mine", "wild"],
        "quality": 1.5,
        "element": "Lightning",
        "roles": {
            "enchantment": {"strength": 3, "defense": 0, "hp": 0, "mp": 8},
            "binding": {"strength": 1, "defense": 1, "hp": 1, "mp": 3},
        },
    },
    "Moonwood": {
        "sources": ["wild", "shop"],
        "quality": 1.25,
        "element": "Light",
        "roles": {
            "core": {"strength": 1, "defense": 2, "hp": 3, "mp": 5},
            "binding": {"strength": 1, "defense": 1, "hp": 2, "mp": 4},
            "lining": {"strength": 0, "defense": 2, "hp": 4, "mp": 6},
        },
    },
    "Bone Resin": {
        "sources": ["drop", "wild"],
        "quality": 1.1,
        "element": "Shadow",
        "roles": {
            "binding": {"strength": 2, "defense": 1, "hp": 4, "mp": 0},
            "lining": {"strength": 0, "defense": 2, "hp": 7, "mp": 0},
            "enchantment": {"strength": 2, "defense": 0, "hp": 3, "mp": 3},
        },
    },
}


CRAFTING_RECIPES = {
    "Steel Ingot": {"Iron Ore": 2, "Coal": 1},
    "Storm Metal": {"Iron Ore": 3, "Thunder Quartz": 1},
}


def recipe_catalog():
    return {
        name: dict(recipe)
        for name, recipe in CRAFTING_RECIPES.items()
    }


def has_materials(inventory, requirements):
    counts = {}
    for item in inventory:
        counts[item.name] = counts.get(item.name, 0) + 1
    return all(counts.get(name, 0) >= quantity
               for name, quantity in requirements.items())


def consume_materials(inventory, requirements):
    if not has_materials(inventory, requirements):
        return False
    remaining = dict(requirements)
    for item in list(inventory):
        if item.name in remaining:
            inventory.remove(item)
            remaining[item.name] -= 1
            if remaining[item.name] == 0:
                del remaining[item.name]
            if not remaining:
                break
    return True


def craft_component(name, inventory):
    requirements = CRAFTING_RECIPES.get(name)
    if requirements is None:
        raise ValueError(f"Unknown crafting recipe: {name}")
    if not consume_materials(inventory, requirements):
        return None
    from items import Item
    component = Item(name, f"A refined crafting component.", 40)
    return component


def calculate_component_bonuses(primary, secondary=None, tertiary=None, slot="blade"):
    result = {"strength": 0, "defense": 0, "hp": 0, "mp": 0}
    for material_name in (primary, secondary, tertiary):
        if not material_name:
            continue
        rule = MATERIALS.get(material_name)
        if rule is None:
            continue
        role_bonus = rule["roles"].get(slot)
        if role_bonus:
            for stat in result:
                result[stat] += role_bonus[stat]
    return result


def calculate_role_bonuses(component_roles):
    result = {"strength": 0, "defense": 0, "hp": 0, "mp": 0}
    for material_name, role in component_roles:
        if not material_name:
            continue
        rule = MATERIALS.get(material_name)
        if rule is None:
            continue
        role_bonus = rule["roles"].get(role)
        if role_bonus:
            for stat in result:
                result[stat] += role_bonus[stat]
    return result


def get_material_sources():
    return {
        name: list(rule["sources"])
        for name, rule in MATERIALS.items()
    }


def gather_wild_material(area=None):
    candidates = [
        name for name, rule in MATERIALS.items()
        if "wild" in rule["sources"] or "mine" in rule["sources"]
    ]
    if not candidates:
        return None
    name = random.choice(candidates)
    return name
