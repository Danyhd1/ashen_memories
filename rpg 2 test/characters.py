from jobs import create_job
from items import Equipment
from races import RACES

class Character:
    def __init__(
        self,
        name,
        job,
        max_hp,
        max_mp,
        strength,
        defense,
        race="Human",
        custom_job=None,
        abilities=None,
        magic_type=None,
        template=None,
        ):

        self.name = name
        self.race = race if race in RACES else "Human"
        race_bonuses = RACES[self.race]
        if custom_job:
            self.job = create_job(f"Custom:{custom_job}")
        elif template:
            self.job = create_job(template)
        else:
            self.job = create_job(job)

        if self.job is None:
            self.job = create_job("Warrior")
            if job:
                self.job.name = job

        self.base_max_hp = max_hp
        self.base_max_mp = max_mp
        self.base_strength = strength
        self.base_defense = defense
        self.custom_job_name = custom_job
        self.abilities = list(abilities or [])
        self.magic_type = magic_type or "none"
        self.template = template
        self.skill_points = 0
        self.learned_skills = []

        self.level = 1
        self.exp = 0

        self.max_hp = max(1, max_hp + race_bonuses["max_hp"])
        self.hp = self.max_hp

        self.max_mp = max(0, max_mp + race_bonuses["max_mp"])
        self.mp = self.max_mp

        self.strength = max(1, strength + race_bonuses["strength"])
        self.defense = max(0, defense + race_bonuses["defense"])

        self.weapon = None
        self.armor = None
        self.helm = None
        self.accessory_1 = None
        self.accessory_2 = None

        self.gold = 100
        self.inventory = []

        self.spells = []
        self.status_effects = {}
        self.defending = False

    def equip(self, equipment):
        if not isinstance(equipment, Equipment):
            return False
        slot = equipment.slot
        if slot == "accessory":
            if self.accessory_1 is None:
                slot = "accessory_1"
            elif self.accessory_1 is equipment:
                slot = "accessory_1"
            elif self.accessory_2 is None:
                slot = "accessory_2"
            elif self.accessory_2 is equipment:
                slot = "accessory_2"
            else:
                slot = "accessory_1"

        current = getattr(self, slot)
        if current is equipment:
            return False

        if current is not None:
            self.strength -= current.strength_bonus
            self.defense -= current.defense_bonus
            self.max_hp -= current.max_hp_bonus
            self.max_mp -= current.max_mp_bonus

        setattr(self, slot, equipment)
        self.strength += equipment.strength_bonus
        self.defense += equipment.defense_bonus
        self.max_hp += equipment.max_hp_bonus
        self.max_mp += equipment.max_mp_bonus
        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)
        return True

    def is_alive(self):
        return self.hp > 0

    def apply_status(self, status, duration):
        if status and duration > 0:
            self.status_effects[status] = max(
                duration,
                self.status_effects.get(status, 0)
            )

    def has_status(self, status):
        return self.status_effects.get(status, 0) > 0

    def heal(self, amount):
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def take_damage(self, amount):
        self.hp -= amount

        if self.hp < 0:
            self.hp = 0

    def restore_mp(self):
        self.mp = self.max_mp

    def full_restore(self):
        self.hp = self.max_hp
        self.mp = self.max_mp

 