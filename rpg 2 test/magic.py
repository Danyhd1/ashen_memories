import random
from elements import element_multiplier


class Spell:

    def __init__(
        self,
        name,
        mp_cost,
        power,
        description,
        spell_type,
        target_type="enemy",
        status=None,
        duration=0,
        spell_level=0,
        element="Neutral"
    ):

        self.name = name
        self.mp_cost = mp_cost
        self.power = power
        self.description = description
        self.spell_type = spell_type
        self.target_type = target_type
        self.status = status
        self.duration = duration
        self.spell_level = spell_level
        self.element = element

    def cast(self, caster, target, charge_cost=True):

        if charge_cost and caster.mp < self.mp_cost:
            print(f"{caster.name} does not have enough MP.")
            return False

        if charge_cost:
            caster.mp -= self.mp_cost
        print(f"{caster.name} uses {self.name}!")

        if self.spell_type == "damage":
            damage = random.randint(
                max(1, int(self.power * 0.8)),
                max(1, int(self.power * 1.2))
            )
            multiplier = element_multiplier(
                self.element,
                getattr(target, "element", "Neutral"),
                getattr(target, "enemy_type", "Beast")
            )
            damage = max(1, int(damage * multiplier))
            target.take_damage(damage)
            print(f"{target.name} takes {damage} damage.")

        elif self.spell_type == "piercing":
            damage = random.randint(
                max(1, int(self.power * 0.8)),
                max(1, int(self.power * 1.2))
            )
            target.take_damage(damage)
            print(f"{self.name} ignores armor and deals {damage} damage to {target.name}.")

        elif self.spell_type == "heal":
            healing = random.randint(
                max(1, int(self.power * 0.8)),
                max(1, int(self.power * 1.2))
            )
            target.heal(healing)
            print(f"{target.name} recovers {healing} HP.")

        elif self.spell_type == "buff":
            target.apply_status(self.status, self.duration)
            print(f"{target.name} gains {self.status.replace('_', ' ')}.")

        elif self.spell_type == "debuff":
            target.apply_status(self.status, self.duration)
            print(f"{target.name} is afflicted with {self.status.replace('_', ' ')}.")

        else:
            print(f"Unknown ability type: {self.spell_type}")
            if charge_cost:
                caster.mp += self.mp_cost
            return False

        if self.status and self.spell_type == "damage" and target.is_alive():
            target.apply_status(self.status, self.duration)
            print(f"{target.name} is afflicted with {self.status.replace('_', ' ')}.")

        return True


SPELLS = {
    "Fire": Spell("Fire", 5, 20, "A basic fire spell.", "damage", spell_level=1, element="Fire"),
    "Blizzard": Spell("Blizzard", 6, 25, "A focused ice spell.", "damage", spell_level=2, element="Ice"),
    "Thunder": Spell("Thunder", 8, 35, "A powerful lightning spell.", "damage", spell_level=3, element="Lightning"),
    "Cure": Spell("Cure", 4, 25, "Restores HP.", "heal", "ally", spell_level=1),
    "Greater Cure": Spell("Greater Cure", 9, 55, "Restores a large amount of HP.", "heal", "ally", spell_level=3),
    "Firestorm": Spell("Firestorm", 12, 18, "Damages every enemy.", "damage", "all_enemies", spell_level=4),
    "Heal All": Spell("Heal All", 12, 20, "Restores the entire party.", "heal", "all_allies", spell_level=5),
    "Protect": Spell("Protect", 5, 0, "Reduces incoming damage for three turns.", "buff", "ally", "protected", 3, 1),
    "Poison Dart": Spell("Poison Dart", 4, 10, "Deals damage and may poison the target.", "damage", "enemy", "poison", 3),
    "Power Strike": Spell("Power Strike", 0, 30, "A heavy physical attack.", "damage"),
    "Shield Bash": Spell("Shield Bash", 0, 20, "Damages and staggers an enemy.", "damage", "enemy", "stagger", 1),
    "Backstab": Spell("Backstab", 0, 40, "A precise, high-damage attack.", "damage"),
    "Guard Stance": Spell("Guard Stance", 0, 0, "Raises defense for three turns.", "buff", "self", "guarded", 3),
    "Smoke Bomb": Spell("Smoke Bomb", 0, 0, "Improves the party's chance to escape.", "buff", "self", "escape_boost", 2),
    "First Aid": Spell("First Aid", 0, 18, "A quick, limited healing technique.", "heal", "ally"),
    "Battle Cry": Spell("Battle Cry", 0, 0, "Raises the party's attack for three turns.", "buff", "all_allies", "empowered", 3),
    "Drain": Spell("Drain", 6, 18, "Damages an enemy and restores the caster.", "drain"),
    "Holy Strike": Spell("Holy Strike", 0, 38, "A radiant blow that staggers an enemy.", "damage", "enemy", "stagger", 1),
    "Sanctuary": Spell("Sanctuary", 8, 0, "Protects the whole party.", "buff", "all_allies", "protected", 3),
    "Aimed Shot": Spell("Aimed Shot", 0, 36, "A precise shot that ignores armor.", "piercing"),
    "Multishot": Spell("Multishot", 5, 15, "Fires at every enemy.", "damage", "all_enemies"),
    "Summon Eidolon": Spell("Summon Eidolon", 10, 45, "Calls an eidolon to strike every enemy.", "damage", "all_enemies"),
    "Spirit Mend": Spell("Spirit Mend", 7, 35, "Calls a spirit to heal the party.", "heal", "all_allies")
}


SPELL_LEVEL_RULES = {
    "none": 0,
    "low": 1,
    "medium": 3,
    "full": 5
}


def get_spell_level_limit(magic_type):
    return SPELL_LEVEL_RULES.get(magic_type, 0)


def get_spell_slots(magic_type, character_level):
    max_level = get_spell_level_limit(magic_type)
    if max_level == 0:
        return {}
    character_level = max(1, character_level)
    slots = {}
    for spell_level in range(1, max_level + 1):
        if character_level >= spell_level:
            slots[spell_level] = max(1, 2 + (character_level - spell_level) // 2)
    return slots


def register_spell(name, mp_cost, power, description, spell_type,
                   target_type="enemy", status=None, duration=0, spell_level=1,
                   element="Neutral"):
    spell = Spell(
        name, mp_cost, power, description, spell_type,
        target_type, status, duration, spell_level, element
    )
    SPELLS[name] = spell
    return create_spell(name)


def register_ability(name, mp_cost, power, description, spell_type,
                     target_type="enemy", status=None, duration=0,
                     unlock_level=1):
    ability = Spell(
        name,
        mp_cost,
        power,
        description,
        spell_type,
        target_type,
        status,
        duration,
        spell_level=0
    )
    SPELLS[name] = ability
    ABILITY_UNLOCK_LEVELS[name] = unlock_level
    return create_spell(name)


ABILITY_UNLOCK_LEVELS = {
    "Power Strike": 1,
    "Guard Stance": 1,
    "Shield Bash": 4,
    "Battle Cry": 7,
    "Backstab": 1,
    "Poison Dart": 1,
    "Smoke Bomb": 4,
    "Drain": 7,
}


JOB_SKILLS = {
    "Warrior": {
        1: ["Power Strike", "Guard Stance"],
        4: ["Shield Bash"],
        7: ["Battle Cry"]
    },
    "Thief": {
        1: ["Backstab", "Poison Dart"],
        4: ["Smoke Bomb"],
        7: ["Drain"]
    },
    "White Mage": {
        1: ["First Aid", "Protect"],
        4: ["Greater Cure"],
        7: ["Heal All"]
    },
    "Black Mage": {
        1: ["Blizzard"],
        4: ["Thunder"],
        7: ["Firestorm"]
    },
    "Paladin": {
        1: ["Holy Strike", "Guard Stance"],
        4: ["Sanctuary"],
        7: ["Battle Cry"]
    },
    "Ranger": {
        1: ["Aimed Shot"],
        4: ["Multishot"],
        7: ["Poison Dart"]
    },
    "Summoner": {
        1: ["Summon Eidolon"],
        4: ["Spirit Mend"],
        7: ["Firestorm"]
    }
}


def create_spell(name):
    spell = SPELLS.get(name)
    if spell is None:
        return None

    return Spell(
        spell.name,
        spell.mp_cost,
        spell.power,
        spell.description,
        spell.spell_type,
        spell.target_type,
        spell.status,
        spell.duration,
        spell.spell_level,
        spell.element
    )


def get_combat_abilities(character):
    abilities = list(character.spells)
    from skills import get_learned_skill_abilities
    abilities.extend(get_learned_skill_abilities(character))
    ability_unlocks = getattr(character, "ability_unlocks", {})
    for ability_name, unlock_level in ability_unlocks.items():
        if character.level >= unlock_level:
            if ability_name not in {ability.name for ability in abilities}:
                ability = create_spell(ability_name)
                if ability is not None:
                    abilities.append(ability)
    for ability_name in getattr(character, "abilities", []):
        if ability_name not in {ability.name for ability in abilities}:
            ability = create_spell(ability_name)
            if ability is not None:
                abilities.append(ability)
    unlocked_names = []

    for level, names in JOB_SKILLS.get(character.job.name, {}).items():
        if character.level >= level:
            unlocked_names.extend(names)

    existing_names = {ability.name for ability in abilities}
    for name in unlocked_names:
        if name not in existing_names:
            ability = create_spell(name)
            if ability is not None:
                abilities.append(ability)
                existing_names.add(name)

    magic_type = getattr(character, "magic_type", "none")
    spell_limit = get_spell_level_limit(magic_type)
    learned = []
    for ability in abilities:
        if getattr(ability, "spell_level", 0) > 0:
            if magic_type != "none" and ability.spell_level <= spell_limit:
                if character.level >= ability.spell_level:
                    learned.append(ability)
        else:
            learned.append(ability)
    return learned
