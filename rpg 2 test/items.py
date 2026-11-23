class Item:
    def __init__(
        self,
        name,
        description,
        value
    ):
        self.name = name
        self.description = description
        self.value = value


class Equipment(Item):
    def __init__(
        self,
        name,
        description,
        value,
        slot,
        strength_bonus=0,
        defense_bonus=0,
        max_hp_bonus=0,
        max_mp_bonus=0
    ):
        super().__init__(name, description, value)
        self.slot = slot
        self.strength_bonus = strength_bonus
        self.defense_bonus = defense_bonus
        self.max_hp_bonus = max_hp_bonus
        self.max_mp_bonus = max_mp_bonus

    def copy(self):
        item = Equipment(
            self.name,
            self.description,
            self.value,
            self.slot,
            self.strength_bonus,
            self.defense_bonus,
            self.max_hp_bonus,
            self.max_mp_bonus
        )
        for attribute in (
            "character_level",
            "crafting_tier",
            "element",
            "weapon_type",
            "armor_type",
            "material"
            ,"crafting_components"
        ):
            if hasattr(self, attribute):
                setattr(item, attribute, getattr(self, attribute))
        return item


CRAFTED_ITEMS = {}


class Consumable(Item):
    def __init__(
        self,
        name,
        description,
        value,
        heal_amount=0
    ):
        super().__init__(
            name,
            description,
            value
        )

        self.heal_amount = heal_amount


    def use(self, target):

        if self.heal_amount > 0:

            target.heal(
                self.heal_amount
            )

            print(
                f"{target.name} "
                f"recovered "
                f"{self.heal_amount} HP."
            )


def create_item(item_name):
    if item_name in CRAFTED_ITEMS:
        return CRAFTED_ITEMS[item_name].copy()

    items = {
        "Iron Ore": Item("Iron Ore", "Raw ore usable in weapons and armor.", 6),
        "Coal": Item("Coal", "Smelting fuel.", 4),
        "Steel Ingot": Item("Steel Ingot", "A refined metal component.", 30),
        "Mithril Thread": Item("Mithril Thread", "Fine magical thread.", 65),
        "Dragon Scale": Item("Dragon Scale", "A rare fire-resistant scale.", 100),
        "Frost Crystal": Item("Frost Crystal", "A cold elemental crystal.", 85),
        "Storm Metal": Item("Storm Metal", "A refined lightning-conductive alloy.", 90),
        "Thunder Quartz": Item("Thunder Quartz", "A charged crystal.", 45),
        "Moonwood": Item("Moonwood", "Pale wood with magical flexibility.", 35),
        "Bone Resin": Item("Bone Resin", "A durable resin collected from old remains.", 25),

        "Potion":
        Consumable(
            "Potion",
            "Restores 30 HP.",
            50,
            heal_amount=30
        ),

        "Hi-Potion":
        Consumable(
            "Hi-Potion",
            "Restores 75 HP.",
            150,
            heal_amount=75
        ),
        "Slime Gel":
        Item(
            "Slime Gel",
            "A useful alchemical material collected from slimes.",
            8
        ),
        "Goblin Ear":
        Item(
            "Goblin Ear",
            "Proof that a goblin was defeated.",
            3
        ),
        "Red Knife Insignia":
        Item(
            "Red Knife Insignia",
            "A marked token carried by the Red Knives bandits.",
            12
        ),
        "Wraith Essence":
        Item(
            "Wraith Essence",
            "A cold fragment of spectral energy.",
            15
        ),
        "Wyvern Scale":
        Item(
            "Wyvern Scale",
            "A tough scale prized by armorers.",
            25
        ),
        "Aegis of Dawn":
        Equipment(
            "Aegis of Dawn",
            "Legendary armor blessed by the arena's first champion.",
            0,
            "armor",
            defense_bonus=8,
            max_hp_bonus=30
        ),
        "Windrunner Bow":
        Equipment(
            "Windrunner Bow",
            "Legendary bow that strikes with uncanny force.",
            0,
            "weapon",
            strength_bonus=10
        ),
        "Starcaller Grimoire":
        Equipment(
            "Starcaller Grimoire",
            "A legendary tome that deepens a summoner's reserves.",
            0,
            "weapon",
            strength_bonus=5,
            max_mp_bonus=30
        ),
        "Iron Sword":
        Equipment("Iron Sword", "A reliable one-handed sword.", 75, "weapon",
                  strength_bonus=3),
        "Oak Staff":
        Equipment("Oak Staff", "A sturdy focus for low-level magic.", 70, "weapon",
                  strength_bonus=1, max_mp_bonus=5),
        "Leather Armor":
        Equipment("Leather Armor", "Flexible traveling armor.", 65, "armor",
                  defense_bonus=3, max_hp_bonus=5),
        "Chain Mail":
        Equipment("Chain Mail", "Heavy mail for front-line defense.", 120, "armor",
                  defense_bonus=6, max_hp_bonus=10),
        "Traveler's Helm":
        Equipment("Traveler's Helm", "A common protective helm.", 55, "helm",
                  defense_bonus=2),
        "Mage Circlet":
        Equipment("Mage Circlet", "A circlet that deepens spell reserves.", 90, "helm",
                  defense_bonus=1, max_mp_bonus=8),
        "Iron Ring":
        Equipment("Iron Ring", "Adds a small amount of physical power.", 60, "accessory",
                  strength_bonus=2),
        "Guardian Charm":
        Equipment("Guardian Charm", "Raises vitality and defense.", 80, "accessory",
                  defense_bonus=2, max_hp_bonus=8),
        "Spellstone":
        Equipment("Spellstone", "Stores magical energy.", 100, "accessory",
                  max_mp_bonus=12)
    }

    return items.get(item_name)
