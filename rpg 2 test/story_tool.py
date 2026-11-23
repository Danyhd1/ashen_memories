import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUESTS_FILE = ROOT / "data" / "quests.json"
EVENTS_FILE = ROOT / "data" / "world_events.json"


def create_template(title="The Shattered Crown"):
    return {
        "title": title,
        "premise": "An ancient crown has fractured, and rival powers race to gather its pieces.",
        "acts": [
            {
                "name": "Act I: The Broken Road",
                "objective": "Find the first heirloom and learn who broke the crown.",
                "dialogue": [
                    "The road has gone quiet since the crown vanished.",
                    "Each shard carries a memory the realms would rather forget."
                ]
            }
        ],
        "quests": [
            {
                "id": "story_opening",
                "name": "The Missing Heirloom",
                "type": "fetch",
                "target": "Slime Gel",
                "goal": 1,
                "description": "Recover the first clue to the missing crown.",
                "prerequisites": [],
                "reward_gold": 75,
                "reward_exp": 30
            }
        ],
        "events": [
            {
                "id": "story_roadmarker",
                "map": "world_map",
                "x": 4,
                "y": 4,
                "name": "A Road of Ash",
                "type": "story",
                "text": "A black feather is pinned beneath a broken royal sign.",
                "gold": 25
            }
        ]
    }


def load_story(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_story(story):
    errors = []
    if not story.get("title"):
        errors.append("Story title is required.")
    if not story.get("premise"):
        errors.append("Story premise is required.")
    if not story.get("acts"):
        errors.append("Story must contain at least one act.")
    quest_ids = set()
    for quest in story.get("quests", []):
        for field in ("id", "name", "type", "target", "goal"):
            if field not in quest:
                errors.append(f"Quest is missing '{field}'.")
        if quest.get("id") in quest_ids:
            errors.append(f"Duplicate quest id: {quest.get('id')}")
        quest_ids.add(quest.get("id"))
    for event in story.get("events", []):
        for field in ("id", "map", "x", "y", "name", "type", "text"):
            if field not in event:
                errors.append(f"Event is missing '{field}'.")
    return errors


def export_story(story, quests_path=QUESTS_FILE, events_path=EVENTS_FILE):
    errors = validate_story(story)
    if errors:
        raise ValueError("; ".join(errors))

    with open(quests_path, "r", encoding="utf-8") as file:
        quests = json.load(file)
    for quest in story.get("quests", []):
        quest_id = quest["id"]
        quests[quest_id] = {
            "id": quest_id,
            "name": quest["name"],
            "type": quest["type"],
            "target": quest["target"],
            "goal": quest["goal"],
            "description": quest.get("description", ""),
            "prerequisites": quest.get("prerequisites", []),
            "reward_gold": quest.get("reward_gold", 0),
            "reward_exp": quest.get("reward_exp", 0),
            "reward_items": quest.get("reward_items", []),
            "reward_jobs": quest.get("reward_jobs", []),
            "destination": quest.get("destination")
        }
    with open(quests_path, "w", encoding="utf-8") as file:
        json.dump(quests, file, indent=4)
        file.write("\n")

    with open(events_path, "r", encoding="utf-8") as file:
        events = json.load(file)
    for event in story.get("events", []):
        event_id = event["id"]
        events[event_id] = {
            key: value for key, value in event.items() if key != "id"
        }
    with open(events_path, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4)
        file.write("\n")


def interactive_create(output_path):
    title = input("Story title: ").strip() or "The Shattered Crown"
    premise = input("Story premise: ").strip()
    story = create_template(title)
    if premise:
        story["premise"] = premise
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(story, file, indent=4)
        file.write("\n")
    print(f"Story saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Create and export game stories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a story template.")
    init_parser.add_argument("path", nargs="?", default="custom_story.json")

    validate_parser = subparsers.add_parser("validate", help="Validate a story.")
    validate_parser.add_argument("path")

    export_parser = subparsers.add_parser("export", help="Export quests and events.")
    export_parser.add_argument("path")

    subparsers.add_parser("interactive", help="Create a story interactively.")

    args = parser.parse_args()
    if args.command == "init":
        path = ROOT / args.path
        with open(path, "w", encoding="utf-8") as file:
            json.dump(create_template(), file, indent=4)
            file.write("\n")
        print(f"Story template saved to {path}")
    elif args.command == "validate":
        story = load_story(args.path)
        errors = validate_story(story)
        if errors:
            print("Story is invalid:")
            for error in errors:
                print(f"- {error}")
            return 1
        print("Story is valid.")
    elif args.command == "export":
        story = load_story(args.path)
        export_story(story)
        print("Story quests and events exported.")
    else:
        interactive_create(ROOT / "custom_story.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
