from dataclasses import dataclass, replace


SKILL_POINT_RULES = {
    "none": 6,
    "low": 4,
    "medium": 3,
    "full": 2,
}


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    description: str
    cost: int
    unlock_level: int
    prerequisites: tuple
    category: str
    base_power: int
    growth: int
    spell_type: str = "damage"
    target_type: str = "enemy"
    status: str = None
    duration: int = 0
    mp_cost: int = 0
    element: str = "Neutral"


SKILL_REGISTRY = {}


def register_skill(name, description="", cost=1, unlock_level=1,
                   prerequisites=(), category="Combat", base_power=10,
                   growth=2, spell_type="damage", target_type="enemy",
                   status=None, duration=0, mp_cost=0, element="Neutral",
                   skill_id=None):
    skill_id = skill_id or name.lower().replace(" ", "_")
    skill = Skill(
        skill_id,
        name,
        description,
        cost,
        unlock_level,
        tuple(prerequisites),
        category,
        base_power,
        growth,
        spell_type,
        target_type,
        status,
        duration,
        mp_cost,
        element,
    )
    SKILL_REGISTRY[skill_id] = skill
    return skill


# Core skill trees.
register_skill("Quick Strike", "A reliable physical technique.", 1, 1,
               (), "Power", 12, 3)
register_skill("Vital Conditioning", "Permanently improves the learner.", 1, 2,
               ("quick_strike",), "Vigor", 5, 1, "buff", "self", "guarded", 3)
register_skill("Precision", "A precise strike that ignores armor.", 2, 4,
               ("quick_strike",), "Power", 20, 4, "piercing")
register_skill("Battle Mastery", "Mastery of sustained combat.", 3, 7,
               ("precision", "vital_conditioning"), "Mastery", 35, 6)

register_skill("Arcane Spark", "A basic magical attack.", 1, 1,
               (), "Magic", 10, 3, "damage", "enemy", element="Fire")
register_skill("Arcane Study", "Deepens magical reserves.", 1, 2,
               ("arcane_spark",), "Magic", 8, 2, "buff", "self")
register_skill("Elemental Burst", "A stronger elemental attack.", 2, 5,
               ("arcane_study",), "Magic", 24, 5, "damage", "enemy", mp_cost=4)
register_skill("Archmage's Crown", "The pinnacle of spell mastery.", 3, 9,
               ("elemental_burst",), "Mastery", 45, 7, "damage", "all_enemies", mp_cost=12)

register_skill("Healer's Hands", "Restores an ally.", 1, 2,
               (), "Healing", 16, 4, "heal", "ally", mp_cost=3)
register_skill("Protective Rite", "Raises an ally's defenses.", 1, 3,
               ("healers_hands",), "Healing", 0, 0, "buff", "ally", "protected", 3, 4)
register_skill("Mass Mend", "Heals the entire party.", 3, 6,
               ("protective_rite",), "Healing", 26, 5, "heal", "all_allies", mp_cost=8)

register_skill("Shadowstep", "A fast, evasive attack.", 1, 2,
               (), "Stealth", 14, 3)
register_skill("Venom Edge", "An attack that applies poison.", 2, 5,
               ("shadowstep",), "Stealth", 18, 4, "damage", "enemy", "poison", 3)
register_skill("Night Reign", "A masterful shadow technique.", 3, 8,
               ("venom_edge",), "Mastery", 38, 6)


def get_skill_points_per_level(magic_type):
    return SKILL_POINT_RULES.get(magic_type, 6)


def can_learn_skill(character, skill):
    if character.level < skill.unlock_level:
        return False
    if skill.id in getattr(character, "learned_skills", []):
        return False
    if getattr(character, "skill_points", 0) < skill.cost:
        return False
    learned = set(getattr(character, "learned_skills", []))
    return all(prerequisite in learned for prerequisite in skill.prerequisites)


def learn_skill(character, skill_id):
    skill = SKILL_REGISTRY.get(skill_id)
    if skill is None:
        raise ValueError(f"Unknown skill: {skill_id}")
    if not can_learn_skill(character, skill):
        return None
    character.skill_points -= skill.cost
    character.learned_skills.append(skill.id)
    apply_skill_attribute(character, skill)
    return skill


def apply_skill_attribute(character, skill):
    if skill.category == "Vigor":
        character.max_hp += skill.base_power
        character.hp = min(character.hp + skill.base_power, character.max_hp)
    elif skill.category == "Magic":
        character.max_mp += skill.base_power // 2
        character.mp = min(character.mp + skill.base_power // 2, character.max_mp)
    elif skill.category == "Power":
        if skill.id == "precision":
            character.strength += 1


def get_skill_power(skill, character_level):
    return skill.base_power + max(0, character_level - skill.unlock_level) * skill.growth


def get_learned_skill_abilities(character):
    from magic import Spell

    abilities = []
    for skill_id in getattr(character, "learned_skills", []):
        skill = SKILL_REGISTRY.get(skill_id)
        if skill is None:
            continue
        abilities.append(Spell(
            skill.name,
            skill.mp_cost,
            get_skill_power(skill, character.level),
            skill.description,
            skill.spell_type,
            skill.target_type,
            skill.status,
            skill.duration,
            0,
            skill.element,
        ))
    return abilities


def create_skill_tree(root_name, root_skill, branches):
    register_skill(
        root_skill["name"],
        root_skill.get("description", ""),
        root_skill.get("cost", 1),
        root_skill.get("unlock_level", 1),
        root_skill.get("prerequisites", []),
        root_skill.get("category", root_name),
        root_skill.get("base_power", 10),
        root_skill.get("growth", 2),
        root_skill.get("spell_type", "damage"),
        root_skill.get("target_type", "enemy"),
        root_skill.get("status"),
        root_skill.get("duration", 0),
        root_skill.get("mp_cost", 0),
        root_skill.get("element", "Neutral"),
        root_skill.get("id"),
    )
    root_id = root_skill.get("id") or root_skill["name"].lower().replace(" ", "_")
    for branch in branches:
        prerequisites = list(branch.get("prerequisites", [root_id]))
        register_skill(
            branch["name"],
            branch.get("description", ""),
            branch.get("cost", 1),
            branch.get("unlock_level", 1),
            tuple(prerequisites),
            branch.get("category", root_name),
            branch.get("base_power", 10),
            branch.get("growth", 2),
            branch.get("spell_type", "damage"),
            branch.get("target_type", "enemy"),
            branch.get("status"),
            branch.get("duration", 0),
            branch.get("mp_cost", 0),
            branch.get("element", "Neutral"),
            branch.get("id"),
        )
