import json
import random
from pathlib import Path

from battle import battle
from arena import run_arena
from enemies import create_enemy
from items import create_item
from quests import open_quest_board
from town import handle_town_tile


MAP_FOLDER = Path(__file__).parent / "maps"
EVENTS_FILE = Path(__file__).parent / "data" / "world_events.json"

current_map = None
current_map_name = None

player_x = 0
player_y = 0


def load_map(
    map_name,
    start_x=None,
    start_y=None
):

    global current_map
    global current_map_name
    global player_x
    global player_y

    map_path = (
        MAP_FOLDER
        / f"{map_name}.json"
    )

    with open(
        map_path,
        "r"
    ) as file:

        current_map = json.load(
            file
        )

    current_map_name = map_name

    if start_x is None:

        player_x = current_map[
            "start_x"
        ]

    else:

        player_x = start_x

    if start_y is None:

        player_y = current_map[
            "start_y"
        ]

    else:

        player_y = start_y


def show_map(party=None):

    print(
        f"\n===== {current_map['name']} =====\n"
    )

    tiles = current_map[
        "tiles"
    ]

    for y in range(
        len(tiles)
    ):

        row = ""

        for x in range(
            len(tiles[y])
        ):

            if (
                x == player_x
                and
                y == player_y
            ):

                row += "P "

            else:
                tile = tiles[y][x]
                if tile == "?" and party is not None:
                    visited = any(
                        event.get("map") == current_map_name
                        and event.get("x") == x
                        and event.get("y") == y
                        and event_id in party.discovered_events
                        for event_id, event in get_location_events().items()
                    )
                    if visited:
                        tile = "."
                row += tile + " "

        print(row)

    print("\nP = You  ? = Special location  F = Forest  G = Graveyard")
    print("M = Mountains  W = Wetlands  T = Town  C = Castle  A = Arena")


def get_current_tile():

    return current_map[
        "tiles"
    ][
        player_y
    ][
        player_x
    ]


def is_walkable(tile):

    if tile == "#":

        return False

    return True


def move_player(direction):

    global player_x
    global player_y

    new_x = player_x
    new_y = player_y

    if direction == "w":

        new_y -= 1

    elif direction == "s":

        new_y += 1

    elif direction == "a":

        new_x -= 1

    elif direction == "d":

        new_x += 1

    tiles = current_map[
        "tiles"
    ]

    if (
        new_x < 0
        or new_y < 0
        or new_y >= len(tiles)
        or new_x >= len(tiles[new_y])
    ):

        print(
            "\nYou cannot go that way."
        )

        return False

    target_tile = tiles[
        new_y
    ][
        new_x
    ]

    if not is_walkable(
        target_tile
    ):

        print(
            "\nYou cannot go that way."
        )

        return False

    player_x = new_x
    player_y = new_y

    return True


def get_tile_key():

    return (
        f"{player_x},"
        f"{player_y}"
    )


def check_transition():

    transitions = current_map.get(
        "transitions",
        {}
    )

    key = get_tile_key()

    if key not in transitions:

        return False

    destination = transitions[
        key
    ]

    load_map(
        destination["map"],
        destination["x"],
        destination["y"]
    )

    return True


def get_encounter_rate(tile):

    rates = current_map.get(
        "encounter_rates",
        {}
    )

    return rates.get(
        tile,
        0.0
    )


def check_for_encounter(tile):

    chance = get_encounter_rate(
        tile
    )

    return (
        random.random()
        < chance
    )


def get_area_name(tile):

    areas = current_map.get(
        "areas",
        {}
    )

    return areas.get(
        tile,
        current_map.get(
            "default_area",
            "Unknown"
        )
    )


def get_location_events():
    with open(EVENTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_location_event():
    for event_id, event in get_location_events().items():
        if (
            event.get("map") == current_map_name
            and event.get("x") == player_x
            and event.get("y") == player_y
        ):
            return event_id, event

    return None, None


def handle_location_event(party, battle_callback=None):
    event_id, event = get_location_event()
    if event is None:
        return False

    if event_id in party.discovered_events:
        return False

    print(f"\n===== {event['name']} =====")
    print(event["text"])

    if event["type"] == "battle":
        enemy = create_enemy(event["enemy"])
        if enemy is None:
            raise ValueError(
                f"Location event '{event_id}' references an unknown enemy."
            )

        if battle_callback is None:
            victory = battle(
                party,
                get_area_name(get_current_tile()),
                enemies=[enemy]
            )
        else:
            victory = battle_callback(
                party,
                get_area_name(get_current_tile()),
                [enemy]
            )
        if victory:
            party.discovered_events.append(event_id)
        return True

    if event["type"] == "shrine":
        for member in party.living_members():
            member.full_restore()
        print("The party is fully restored.")

    if event.get("gold", 0) > 0 and party.members:
        party.members[0].gold += event["gold"]
        print(f"You find {event['gold']} gold.")

    if event.get("item"):
        item_name = event["item"]
        quantity = event.get("quantity", 1)
        if create_item(item_name) is None:
            raise ValueError(
                f"Location event '{event_id}' references unknown item '{item_name}'."
            )
        party.update_quests("collect", item_name, quantity=quantity)

    material_name = event.get("material")
    if material_name:
        quantity = event.get("quantity", 1)
        material = create_item(material_name)
        if material is None:
            raise ValueError(
                f"Location event '{event_id}' references unknown material '{material_name}'."
            )
        if party.members:
            for _ in range(quantity):
                party.members[0].inventory.append(create_item(material_name))
        print(
            f"Collected {quantity} {material_name} "
            f"by {'mining' if event.get('mining') else 'gathering'}."
        )

    party.discovered_events.append(event_id)
    return True


def handle_current_tile(party):

    tile = get_current_tile()

    if current_map_name == "town_map":

        handle_town_tile(
            party,
            tile
        )

    elif current_map_name == "castle_map":

        if tile == "Q":

            open_quest_board(party)

    elif current_map_name == "arena_map" and tile == "R":
        run_arena(party)


def record_location(party):
    party.update_quests(
        "visit",
        current_map_name,
        metadata={
            "x": player_x,
            "y": player_y
        }
    )


def explore(party):

    if current_map is None:

        load_map(
            "world_map"
        )

    while True:

        show_map(party)

        print(
            "\nW A S D = Move"
        )

        print(
            "Q = Quit"
        )

        choice = input(
            "> "
        ).lower()

        if choice == "q":

            break

        if choice not in (
            "w",
            "a",
            "s",
            "d"
        ):

            print(
                "\nInvalid choice."
            )

            continue

        moved = move_player(
            choice
        )

        if not moved:

            continue

        transitioned = (
            check_transition()
        )

        if transitioned:

            record_location(party)
            handle_location_event(party)
            continue

        record_location(party)

        if handle_location_event(party):
            continue

        tile = get_current_tile()

        if check_for_encounter(
            tile
        ):

            area = get_area_name(
                tile
            )

            print(
                "\nA random encounter!"
            )

            battle(
                party,
                area
            )

        else:

            handle_current_tile(
                party
            )