from quests import update_party_quests
from stronghold import Stronghold


class Party:

    def __init__(self):
        self.members = []

        self.quests = []
        self.discovered_events = []
        self.unlocked_jobs = {
            "Warrior",
            "Thief",
            "White Mage",
            "Black Mage"
        }
        self.arena_wins = []
        self.stronghold = Stronghold()

    def add_member(
        self,
        character
    ):
        self.members.append(
            character
        )

    def living_members(self):

        return [

            member

            for member
            in self.members

            if member.is_alive()

        ]

    def is_defeated(self):

        return (
            len(
                self.living_members()
            ) == 0
        )
    def add_quest(
        self,
        quest
    ):

        self.quests.append(
            quest
        )

    def update_quests(self, event_type, target, metadata=None, quantity=1):
        update_party_quests(
            self,
            event_type,
            target,
            metadata=metadata,
            quantity=quantity
        )