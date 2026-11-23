from dataclasses import dataclass


STRONGHOLD_TYPES = {
    "Hideout": "A covert base with shortcuts and covert operations.",
    "Fortress": "A defensible headquarters built for armies and sieges.",
    "Temple": "A sanctuary for healing, faith, and magical rites.",
    "Academy": "A center for training, research, and spellcraft.",
    "Estate": "A prosperous domain that produces wealth and influence.",
}


CATEGORIES = (
    "Defense",
    "Economy",
    "Crafting",
    "Training",
    "Magic",
    "Exploration",
    "Sanctuary",
)


@dataclass(frozen=True)
class StrongholdImprovement:
    id: str
    name: str
    category: str
    description: str
    cost: int
    effect: str
    value: int
    prerequisite: str = ""
    stronghold_types: tuple = ()


def generate_improvements():
    improvements = []
    names = (
        "Wall", "Watchtower", "Workshop", "Library", "Barracks",
        "Garden", "Vault", "Sanctum", "Stable", "Landing",
        "Forge", "Shrine", "Archive", "Courtyard", "Dock",
    )
    suffixes = (
        "I", "II", "III", "IV", "V",
        "VI", "VII", "VIII", "IX", "X",
    )
    index = 0
    for category_index, category in enumerate(CATEGORIES):
        for variation in range(29):
            index += 1
            name_base = names[(variation + category_index) % len(names)]
            suffix = suffixes[variation % len(suffixes)]
            tier = (variation // len(suffixes)) + 1
            cost = 100 + tier * 125 + category_index * 25
            effect = {
                "Defense": "defense",
                "Economy": "gold",
                "Crafting": "crafting",
                "Training": "exp",
                "Magic": "mp",
                "Exploration": "exploration",
                "Sanctuary": "healing",
            }[category]
            prerequisite = ""
            if tier > 1:
                prerequisite = f"{category.lower()}_{tier - 1}_{((variation - 1) % 10) + 1}"
            compatible_types = tuple(
                stronghold_type
                for stronghold_type in STRONGHOLD_TYPES
                if stronghold_type != "Hideout" or category in ("Defense", "Economy", "Exploration")
            )
            improvements.append(StrongholdImprovement(
                id=f"{category.lower()}_{tier}_{(variation % 10) + 1}",
                name=f"{name_base} {suffix}",
                category=category,
                description=f"A tier {tier} {category.lower()} improvement for your stronghold.",
                cost=cost,
                effect=effect,
                value=tier * (category_index + 2),
                prerequisite=prerequisite,
                stronghold_types=compatible_types,
            ))
    # Exactly 203 generated entries here; trim to the requested catalog size.
    return improvements[:200]


STRONGHOLD_IMPROVEMENTS = generate_improvements()


class Stronghold:
    def __init__(self, name="Our Stronghold", stronghold_type="Fortress"):
        if stronghold_type not in STRONGHOLD_TYPES:
            raise ValueError(f"Unknown stronghold type: {stronghold_type}")
        self.name = name
        self.stronghold_type = stronghold_type
        self.level = 1
        self.installed = []
        self.bonuses = {
            "defense": 0,
            "gold": 0,
            "crafting": 0,
            "exp": 0,
            "mp": 0,
            "exploration": 0,
            "healing": 0,
        }

    def get_improvement(self, improvement_id):
        return next(
            (item for item in STRONGHOLD_IMPROVEMENTS if item.id == improvement_id),
            None,
        )

    def can_install(self, improvement):
        if improvement.stronghold_types and self.stronghold_type not in improvement.stronghold_types:
            return False
        if improvement.id in self.installed:
            return False
        if improvement.prerequisite and improvement.prerequisite not in self.installed:
            return False
        return True

    def install(self, improvement_id, gold=0):
        improvement = self.get_improvement(improvement_id)
        if improvement is None:
            raise ValueError(f"Unknown stronghold improvement: {improvement_id}")
        if not self.can_install(improvement):
            return None
        if gold < improvement.cost:
            return None
        self.installed.append(improvement.id)
        self.bonuses[improvement.effect] += improvement.value
        self.level = 1 + len(self.installed) // 10
        return improvement

    def uninstall(self, improvement_id):
        improvement = self.get_improvement(improvement_id)
        if improvement is None or improvement.id not in self.installed:
            return False
        self.installed.remove(improvement.id)
        self.bonuses[improvement.effect] -= improvement.value
        self.level = 1 + len(self.installed) // 10
        return True

    def to_dict(self):
        return {
            "name": self.name,
            "stronghold_type": self.stronghold_type,
            "level": self.level,
            "installed": list(self.installed),
            "bonuses": dict(self.bonuses),
        }

    @classmethod
    def from_dict(cls, data):
        stronghold = cls(
            data.get("name", "Our Stronghold"),
            data.get("stronghold_type", "Fortress"),
        )
        stronghold.installed = [
            improvement_id
            for improvement_id in data.get("installed", [])
            if stronghold.get_improvement(improvement_id) is not None
        ]
        stronghold.level = data.get("level", 1)
        stronghold.bonuses = data.get("bonuses", dict(stronghold.bonuses))
        return stronghold


def apply_stronghold_bonuses(party):
    stronghold = getattr(party, "stronghold", None)
    if stronghold is None:
        return
    for member in party.members:
        member.max_mp = max(
            member.max_mp,
            member.max_mp + stronghold.bonuses["mp"]
        )
        member.max_hp = max(
            member.max_hp,
            member.max_hp + stronghold.bonuses["healing"]
        )
