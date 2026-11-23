import json
from pathlib import Path

from items import create_item
from leveling import gain_exp


QUEST_DATA_PATH = Path(__file__).parent / "data" / "quests.json"


def load_quest_definitions():
    with open(QUEST_DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_quest_definition(quest_id):
    return load_quest_definitions().get(quest_id)


class Quest:

    def __init__(
        self,
        name,
        objective_type,
        target,
        goal,
        quest_id=None,
        description="",
        prerequisites=None,
        reward_gold=0,
        reward_exp=0,
        reward_items=None,
        reward_jobs=None,
        destination=None,
        progress=0,
        completed=False
    ):
        self.quest_id = quest_id or name
        self.name = name
        self.objective_type = objective_type
        self.target = target
        self.goal = goal
        self.description = description
        self.prerequisites = list(prerequisites or [])
        self.reward_gold = reward_gold
        self.reward_exp = reward_exp
        self.reward_items = list(reward_items or [])
        self.reward_jobs = list(reward_jobs or [])
        self.destination = destination or {}
        self.progress = progress
        self.completed = completed

    @classmethod
    def from_definition(cls, definition):
        return cls(
            name=definition["name"],
            objective_type=definition["type"],
            target=definition.get("target", ""),
            goal=definition.get("goal", 1),
            quest_id=definition["id"],
            description=definition.get("description", ""),
            prerequisites=definition.get("prerequisites", []),
            reward_gold=definition.get("reward_gold", 0),
            reward_exp=definition.get("reward_exp", 0),
            reward_items=definition.get("reward_items", []),
            reward_jobs=definition.get("reward_jobs", []),
            destination=definition.get("destination")
        )

    def to_dict(self):
        return {
            "id": self.quest_id,
            "name": self.name,
            "objective_type": self.objective_type,
            "target": self.target,
            "goal": self.goal,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "reward_gold": self.reward_gold,
            "reward_exp": self.reward_exp,
            "reward_items": self.reward_items,
            "reward_jobs": self.reward_jobs,
            "destination": self.destination,
            "progress": self.progress,
            "completed": self.completed
        }

    def update_progress(self, event_type, target, metadata=None, quantity=1):
        if self.completed or quantity <= 0:
            return False

        metadata = metadata or {}

        if self.objective_type in ("kill", "bounty"):
            matches = event_type == "kill" and target == self.target
        elif self.objective_type == "fetch":
            matches = event_type == "collect" and target == self.target
        elif self.objective_type == "escort":
            destination = self.destination
            matches = (
                event_type == "visit"
                and target == destination.get("map")
                and metadata.get("x") == destination.get("x")
                and metadata.get("y") == destination.get("y")
            )
        else:
            matches = event_type == self.objective_type and target == self.target

        if not matches:
            return False

        self.progress = min(self.goal, self.progress + quantity)
        print(f"{self.name}: {self.progress}/{self.goal}")

        if self.progress >= self.goal:
            self.completed = True
            print(f"\nQuest Complete: {self.name}")
            return True

        return False


def available_quests(party):
    definitions = load_quest_definitions()
    existing_ids = {quest.quest_id for quest in party.quests}
    completed_ids = {
        quest.quest_id for quest in party.quests if quest.completed
    }
    available = []

    for quest_id, definition in definitions.items():
        if quest_id in existing_ids:
            continue
        if all(
            prerequisite in completed_ids
            for prerequisite in definition.get("prerequisites", [])
        ):
            available.append(definition)

    return available


def _award_quest_rewards(party, quest):
    if party.members:
        party.members[0].gold += quest.reward_gold

    for member in party.members:
        gain_exp(member, quest.reward_exp)

    for job_name in quest.reward_jobs:
        if job_name not in party.unlocked_jobs:
            party.unlocked_jobs.add(job_name)
            print(f"New job unlocked: {job_name}!")

    for item_name in quest.reward_items:
        item = create_item(item_name)
        if item is None:
            raise ValueError(
                f"Quest '{quest.quest_id}' rewards unknown item '{item_name}'."
            )
        if party.members:
            party.members[0].inventory.append(item)
        print(f"Legendary gear obtained: {item_name}!")

    if quest.reward_gold:
        print(f"Quest reward: {quest.reward_gold} gold.")
    if quest.reward_exp:
        print(f"Quest reward: {quest.reward_exp} EXP for each party member.")


def open_quest_board(party):
    while True:
        quests = available_quests(party)
        print("\n===== QUEST BOARD =====")

        if not quests:
            print("No new contracts are available.")
            return

        for index, definition in enumerate(quests, start=1):
            print(
                f"{index}. {definition['name']} "
                f"[{definition['type'].title()}]"
            )
            print(f"   {definition.get('description', '')}")
            print(
                f"   Reward: {definition.get('reward_gold', 0)} gold, "
                f"{definition.get('reward_exp', 0)} EXP per member"
            )

        print("0. Leave board")
        try:
            choice = int(input("> "))
        except ValueError:
            print("Enter a listed number.")
            continue

        if choice == 0:
            return
        if not 1 <= choice <= len(quests):
            print("Enter a listed number.")
            continue

        selected = quests[choice - 1]
        quest = Quest.from_definition(selected)
        party.add_quest(quest)
        print(f"\nAccepted: {quest.name}")


def show_quest_log(party):
    print("\n===== QUEST LOG =====")
    if not party.quests:
        print("No quests accepted yet. Visit the castle quest board.")
        return

    for quest in party.quests:
        status = "Complete" if quest.completed else "Active"
        print(f"\n{quest.name} [{quest.objective_type.title()} - {status}]")
        if quest.description:
            print(quest.description)
        print(f"Progress: {quest.progress}/{quest.goal}")
        if quest.objective_type == "escort" and quest.destination:
            print(f"Destination: {quest.destination.get('name', quest.target)}")


def update_party_quests(party, event_type, target, metadata=None, quantity=1):
    for quest in party.quests:
        was_completed = quest.completed
        completed_now = quest.update_progress(
            event_type,
            target,
            metadata=metadata,
            quantity=quantity
        )
        if completed_now and not was_completed:
            _award_quest_rewards(party, quest)

    if event_type == "collect" and quantity > 0:
        item = create_item(target)
        if item is not None and party.members:
            party.members[0].inventory.append(item)
            party.members[0].inventory.extend(
                create_item(target) for _ in range(quantity - 1)
            )
            print(f"Collected {quantity} {target}.")
