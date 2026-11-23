import sys

from characters import Character
from party import Party

from save import save_game
from save import load_game

from world import explore
from quests import Quest, get_quest_definition, show_quest_log
from magic import create_spell


# ==========================
# PARTY CREATION
# ==========================

def create_party():

    party = Party()

    print("\n=== PARTY CREATION ===")

    for slot in range(1, 5):

        print(f"\nCharacter #{slot}")

        name = input(
            "Name: "
        )

        print("\nChoose Job")

        print("1. Warrior")
        print("2. Thief")
        print("3. White Mage")
        print("4. Black Mage")

        choice = input("> ")

        if choice == "1":

            character = Character(
                name,
                "Warrior",
                60,
                0,
                10,
                5
            )

        elif choice == "2":

            character = Character(
                name,
                "Thief",
                50,
                0,
                8,
                3
            )

        elif choice == "3":

            character = Character(
                name,
                "White Mage",
                40,
                20,
                4,
                2
            )

        elif choice == "4":

            character = Character(
                name,
                "Black Mage",
                35,
                25,
                3,
                1
            )

        else:

            print(
                "Invalid choice."
            )

            continue

        give_starting_spells(
           character
        )

        party.add_member(
            character
        )

    return party

def give_starting_spells(character):

    if character.job.name == "White Mage":

        character.spells.append(
            create_spell("Cure")
        )

    elif character.job.name == "Black Mage":

        character.spells.append(
            create_spell("Fire")
        )

# ==========================
# PARTY DISPLAY
# ==========================

def show_party(party):

    print("\n===== PARTY =====")

    for member in party.members:

        print(
            f"\n{member.name}"
        )

        print(
            f"Class: {member.job.name}"
        )

        print(
            f"Level: {member.level}"
        )

        print(
            f"HP: "
            f"{member.hp}/{member.max_hp}"
        )

        print(
            f"MP: "
            f"{member.mp}/{member.max_mp}"
        )

        print(
            f"EXP: {member.exp}"
        )


# ==========================
# PARTY LEADER
# ==========================

def get_party_leader(party):

    return party.members[0]

# ==========================
# QUESTS
# ==========================


def show_quests(party):

    show_quest_log(party)


# ==========================
# MAIN
# ==========================

def main():

    party = None
    hero = None

    while True:

        print("\n===== MAIN MENU =====")

        print("1. New Game")
        print("2. Load Game")
        print("3. Quit")

        choice = input("> ")

        if choice == "1":

            party = create_party()

            first_contract = get_quest_definition("first_contract")
            party.add_quest(Quest.from_definition(first_contract))

            hero = get_party_leader(
                party
            )

            break

        elif choice == "2":

            party = load_game()

            if party:

                hero = get_party_leader(
                    party
                )

                break

        elif choice == "3":

            print(
                "\nThanks for playing!"
            )

            return

        else:

            print(
                "\nInvalid choice."
            )

    while True:

        print("\n===== GAME MENU =====")

        print(
            f"\nLeader: "
            f"{hero.name}"
        )

        print("1. Explore")
        print("2. View Party")
        print("3. View Quests")
        print("4. Save")
        print("5. View Leader Stats")
        print("6. Quit")

        choice = input("> ")

        if choice == "1":

            explore(party)

        elif choice == "2":

            show_party(party)

        elif choice == "3":

            show_quests(party)

        elif choice == "4":

            save_game(party)

        elif choice == "5":

            print(
                f"\nName: "
                f"{hero.name}"
            )

            print(
                f"Job: "
                f"{hero.job.name}"
            )

            print(
                f"Level: "
                f"{hero.level}"
            )

            print(
                f"HP: "
                f"{hero.hp}/{hero.max_hp}"
            )

            print(
                f"MP: "
                f"{hero.mp}/{hero.max_mp}"
            )

            print(
                f"Gold: "
                f"{hero.gold}"
            )

            print(
                f"EXP: "
                f"{hero.exp}"
            )

        elif choice == "6":

            print(
                "\nGoodbye!"
            )

            break

        else:

            print(
                "\nInvalid choice."
            )


# ==========================
# ENTRY POINT
# ==========================

if __name__ == "__main__":
    if "--android" in sys.argv:
        from mobile_server import main as mobile_main
        port_args = [arg for arg in sys.argv if arg.isdigit()]
        sys.argv = [sys.argv[0]] + port_args[:1]
        mobile_main()
    elif "--cli" in sys.argv:
        main()
    else:
        from gui import main as gui_main

        raise SystemExit(gui_main())