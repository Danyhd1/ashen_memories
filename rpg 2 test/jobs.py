class Job:

    def __init__(self, name):
        self.name = name

    def level_up(self, character):
        pass

class Warrior(Job):

    def __init__(self):
        super().__init__("Warrior")

    def level_up(self, character):

        character.max_hp += 12
        character.strength += 3
        character.defense += 2

class Thief(Job):

    def __init__(self):
        super().__init__("Thief")

    def level_up(self, character):

        character.max_hp += 8
        character.strength += 2
        character.defense += 1

class WhiteMage(Job):

    def __init__(self):
        super().__init__("White Mage")

    def level_up(self, character):

        character.max_hp += 5
        character.max_mp += 8
        character.defense += 1



class BlackMage(Job):

    def __init__(self):
        super().__init__("Black Mage")

    def level_up(self, character):

        character.max_hp += 4
        character.max_mp += 10


class Paladin(Job):

    def __init__(self):
        super().__init__("Paladin")

    def level_up(self, character):
        character.max_hp += 10
        character.max_mp += 3
        character.strength += 2
        character.defense += 3


class Ranger(Job):

    def __init__(self):
        super().__init__("Ranger")

    def level_up(self, character):
        character.max_hp += 8
        character.max_mp += 3
        character.strength += 3
        character.defense += 1


class Summoner(Job):

    def __init__(self):
        super().__init__("Summoner")

    def level_up(self, character):
        character.max_hp += 5
        character.max_mp += 12
        character.strength += 1
        character.defense += 1


class CustomJob(Job):

    def __init__(self, name, growth=None):
        super().__init__(name)
        self.growth = growth or {
            "max_hp": 8,
            "max_mp": 4,
            "strength": 2,
            "defense": 1
        }

    def level_up(self, character):
        character.max_hp += self.growth["max_hp"]
        character.max_mp += self.growth["max_mp"]
        character.strength += self.growth["strength"]
        character.defense += self.growth["defense"]


BASE_CLASS_TEMPLATES = {
    "Fighter": {
        "description": "Armored weapon specialist.",
        "stats": (60, 0, 10, 6),
        "growth": {"max_hp": 12, "max_mp": 1, "strength": 3, "defense": 3},
        "magic_type": "none",
        "abilities": ["Power Strike", "Guard Stance"]
    },
    "Thief": {
        "description": "Fast striker and escape artist.",
        "stats": (50, 4, 9, 3),
        "growth": {"max_hp": 8, "max_mp": 3, "strength": 3, "defense": 1},
        "magic_type": "none",
        "abilities": ["Backstab", "Poison Dart"]
    },
    "Paladin": {
        "description": "Holy warrior with limited magic.",
        "stats": (58, 8, 9, 5),
        "growth": {"max_hp": 10, "max_mp": 4, "strength": 2, "defense": 3},
        "magic_type": "low",
        "abilities": ["Holy Strike", "Protect"]
    },
    "Red Mage": {
        "description": "Balanced fighter and spellcaster.",
        "stats": (52, 16, 7, 4),
        "growth": {"max_hp": 8, "max_mp": 6, "strength": 2, "defense": 2},
        "magic_type": "medium",
        "abilities": ["Power Strike", "Fire", "Cure"]
    },
    "Archmage": {
        "description": "Full five-level spellcasting expert.",
        "stats": (38, 30, 4, 2),
        "growth": {"max_hp": 5, "max_mp": 10, "strength": 1, "defense": 1},
        "magic_type": "full",
        "abilities": ["Firestorm", "Greater Cure"]
    }
}


def create_job(job_name):

    jobs = {

        "Warrior": Warrior(),
        "Thief": Thief(),
        "White Mage": WhiteMage(),
        "Black Mage": BlackMage(),
        "Paladin": Paladin(),
        "Ranger": Ranger(),
        "Summoner": Summoner()

    }

    if job_name in jobs:
        return jobs[job_name]

    if job_name in BASE_CLASS_TEMPLATES:
        template = BASE_CLASS_TEMPLATES[job_name]
        growth = template["growth"]
        return CustomJob(job_name, growth)

    if isinstance(job_name, CustomJob):
        return job_name

    if job_name.startswith("Custom:"):
        return CustomJob(job_name.removeprefix("Custom:"))

    return jobs.get(job_name)
