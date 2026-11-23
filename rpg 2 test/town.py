from items import create_item
from items import Equipment
from jobs import create_job
from blacksmith import blacksmith_menu
from stronghold import (
    STRONGHOLD_TYPES,
    STRONGHOLD_IMPROVEMENTS,
)


def get_party_leader(party):

    return party.members[0]


def inn(party):

    leader = get_party_leader(
        party
    )

    cost = 20

    if leader.gold < cost:

        print(
            "\nYou do not have enough gold."
        )

        return

    leader.gold -= cost

    for member in party.members:

        member.full_restore()

    print(
        "\nThe party rests at the inn."
    )

    print(
        "Everyone's HP and MP "
        "have been restored."
    )


def buy_potion(party):

    leader = get_party_leader(
        party
    )

    cost = 50

    if leader.gold < cost:

        print(
            "\nNot enough gold."
        )

        return

    leader.gold -= cost

    potion = create_item(
        "Potion"
    )

    leader.inventory.append(
        potion
    )

    print(
        "\nPotion purchased."
    )


def show_inventory(party):

    leader = get_party_leader(
        party
    )

    print(
        "\n===== INVENTORY ====="
    )

    if not leader.inventory:

        print(
            "Empty"
        )

        return

    for index, item in enumerate(
        leader.inventory,
        start=1
    ):

        print(
            f"{index}. "
            f"{item.name}"
        )


def shop_menu(party):

    while True:

        leader = get_party_leader(
            party
        )

        print(
            "\n===== SHOP ====="
        )

        print(
            f"Gold: {leader.gold}"
        )

        print(
            "1. Buy Potion - 50 gold"
        )
        print("2. Buy Crafting Materials")
        print("3. View Inventory")
        print("4. Leave Shop")

        choice = input(
            "> "
        )

        if choice == "1":

            buy_potion(
                party
            )

        elif choice == "2":
            buyable = ("Iron Ore", "Coal", "Moonwood")
            print("Choose material:")
            for index, material_name in enumerate(buyable, 1):
                material = create_item(material_name)
                print(f"{index}. {material.name} - {material.value} gold")
            try:
                selected = buyable[int(input("> ")) - 1]
            except (ValueError, IndexError):
                print("Invalid material choice.")
                continue
            material = create_item(selected)
            if leader.gold < material.value:
                print("Not enough gold.")
                continue
            leader.gold -= material.value
            leader.inventory.append(material)
            print(f"Purchased {material.name}.")
        elif choice == "3":
            show_inventory(party)
        elif choice == "4":
            return

        else:

            print(
                "\nInvalid choice."
            )


def _choose_member(party):
    while True:
        print("\nChoose a character:")
        for index, member in enumerate(party.members, start=1):
            print(f"{index}. {member.name} - {member.job.name}")
        print("0. Back")

        try:
            choice = int(input("> "))
        except ValueError:
            print("Enter a listed number.")
            continue

        if choice == 0:
            return None
        if 1 <= choice <= len(party.members):
            return party.members[choice - 1]
        print("Enter a listed number.")


def change_jobs(party):
    member = _choose_member(party)
    if member is None:
        return

    available_jobs = sorted(party.unlocked_jobs)
    while True:
        print(f"\n===== JOB CHANGE: {member.name} =====")
        for index, job_name in enumerate(available_jobs, start=1):
            current = " (current)" if member.job.name == job_name else ""
            print(f"{index}. {job_name}{current}")
        print("0. Back")

        try:
            choice = int(input("> "))
        except ValueError:
            print("Enter a listed number.")
            continue

        if choice == 0:
            return
        if not 1 <= choice <= len(available_jobs):
            print("Enter a listed number.")
            continue

        selected_job = available_jobs[choice - 1]
        if selected_job == member.job.name:
            print(f"{member.name} is already a {selected_job}.")
            return

        member.job = create_job(selected_job)
        minimum_mp = {
            "Paladin": 8,
            "Ranger": 6,
            "Summoner": 20
        }.get(selected_job, 0)
        if member.max_mp < minimum_mp:
            member.max_mp = minimum_mp
            member.mp = minimum_mp
        print(
            f"{member.name} changed jobs to {selected_job}. "
            "Current stats are preserved; future level-ups follow the new job."
        )
        return


def manage_equipment(party):
    member = _choose_member(party)
    if member is None:
        return

    equipment = [
        item for item in member.inventory
        if isinstance(item, Equipment)
    ]
    if not equipment:
        print("\nNo equipment to manage.")
        return

    while True:
        print(f"\n===== EQUIPMENT: {member.name} =====")
        print(
            f"Weapon: {member.weapon.name if member.weapon else 'None'}"
        )
        print(
            f"Armor: {member.armor.name if member.armor else 'None'}"
        )
        for index, item in enumerate(equipment, start=1):
            bonuses = []
            if item.strength_bonus:
                bonuses.append(f"+{item.strength_bonus} strength")
            if item.defense_bonus:
                bonuses.append(f"+{item.defense_bonus} defense")
            if item.max_hp_bonus:
                bonuses.append(f"+{item.max_hp_bonus} max HP")
            if item.max_mp_bonus:
                bonuses.append(f"+{item.max_mp_bonus} max MP")
            print(
                f"{index}. Equip {item.name} ({item.slot}; "
                f"{', '.join(bonuses)})"
            )
        print("0. Back")

        try:
            choice = int(input("> "))
        except ValueError:
            print("Enter a listed number.")
            continue

        if choice == 0:
            return
        if not 1 <= choice <= len(equipment):
            print("Enter a listed number.")
            continue

        item = equipment[choice - 1]
        member.equip(item)
        print(f"{member.name} equips {item.name}.")
        return


def skill_menu(party):
    member = get_party_leader(party)
    from skills import SKILL_REGISTRY, can_learn_skill, learn_skill

    while True:
        print(f"\n===== SKILLS: {member.name} =====")
        print(f"Level: {member.level} | Skill points: {member.skill_points}")
        available = [
            skill for skill in SKILL_REGISTRY.values()
            if can_learn_skill(member, skill)
        ]
        if not available:
            print("No skills are currently available.")
        for index, skill in enumerate(available, 1):
            print(
                f"{index}. {skill.name} [{skill.category}] "
                f"- {skill.cost} point(s), level {skill.unlock_level}"
            )
        print("0. Back")
        choice = input("> ").strip()
        if choice == "0":
            return
        try:
            skill = available[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid skill choice.")
            continue
        learned = learn_skill(member, skill.id)
        if learned:
            print(f"{member.name} learned {learned.name}.")


def stronghold_menu(party):
    while True:
        stronghold = party.stronghold
        print("\n===== STRONGHOLD =====")
        print(f"{stronghold.name} [{stronghold.stronghold_type}] - Level {stronghold.level}")
        print(f"Installed improvements: {len(stronghold.installed)}")
        print("1. Rename stronghold")
        print("2. Change stronghold type")
        print("3. Browse improvements")
        print("4. View active bonuses")
        print("0. Leave")
        choice = input("> ").strip()

        if choice == "1":
            name = input("Stronghold name: ").strip()
            if name:
                stronghold.name = name
        elif choice == "2":
            types = list(STRONGHOLD_TYPES)
            for index, name in enumerate(types, 1):
                print(f"{index}. {name}")
            try:
                stronghold.stronghold_type = types[int(input("> ")) - 1]
            except (ValueError, IndexError):
                print("Invalid stronghold type.")
        elif choice == "3":
            available = [
                improvement
                for improvement in STRONGHOLD_IMPROVEMENTS
                if stronghold.can_install(improvement)
            ]
            for index, improvement in enumerate(available[:20], 1):
                print(
                    f"{index}. {improvement.name} "
                    f"[{improvement.category}] - {improvement.cost} gold"
                )
            print("0. Back")
            if not available:
                print("No compatible improvements are currently available.")
                continue
            try:
                selected_index = int(input("> "))
            except ValueError:
                continue
            if selected_index == 0:
                continue
            if not 1 <= selected_index <= min(20, len(available)):
                print("Invalid improvement.")
                continue
            improvement = available[selected_index - 1]
            leader = get_party_leader(party)
            installed = stronghold.install(improvement.id, leader.gold)
            if installed is None:
                print("Not enough gold or prerequisites are missing.")
            else:
                leader.gold -= improvement.cost
                print(f"Installed {improvement.name}.")
        elif choice == "4":
            for effect, value in stronghold.bonuses.items():
                print(f"{effect.title()}: +{value}")
        elif choice == "0":
            return


def job_guild(party):
    while True:
        print("\n===== GUILD OF MASTERS =====")
        print("1. Change Job")
        print("2. Manage Equipment")
        print("3. View Unlocked Jobs")
        print("4. Visit Blacksmith")
        print("5. Craft Components")
        print("6. Manage Stronghold")
        print("7. Learn Skills")
        print("0. Leave")
        choice = input("> ").strip()

        if choice == "1":
            change_jobs(party)
        elif choice == "2":
            manage_equipment(party)
        elif choice == "3":
            print("Unlocked jobs: " + ", ".join(sorted(party.unlocked_jobs)))
        elif choice == "4":
            blacksmith_menu(party)
        elif choice == "5":
            from crafting import CRAFTING_RECIPES, craft_component
            crafter = get_party_leader(party)
            recipes = list(CRAFTING_RECIPES)
            for index, name in enumerate(recipes, 1):
                requirements = ", ".join(
                    f"{quantity} {material}"
                    for material, quantity in CRAFTING_RECIPES[name].items()
                )
                print(f"{index}. {name} ({requirements})")
            try:
                selected = recipes[int(input("> ")) - 1]
            except (ValueError, IndexError):
                print("Invalid recipe choice.")
                continue
            component = craft_component(selected, crafter.inventory)
            if component is None:
                print("Missing required materials.")
            else:
                crafter.inventory.append(component)
                print(f"Crafted {component.name}.")
        elif choice == "6":
            stronghold_menu(party)
        elif choice == "7":
            skill_menu(party)
        elif choice == "0":
            return
        else:
            print("Invalid choice.")


def handle_town_tile(
    party,
    tile
):

    if tile == "I":

        inn(
            party
        )

    elif tile == "S":

        shop_menu(
            party
        )

    elif tile == "J":

        job_guild(
            party
        )