import json
import mimetypes
import os
import random
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import battle
import world
from characters import Character
from enemies import create_enemy
from party import Party
from quests import Quest, get_quest_definition
from save import load_game, save_game


ROOT = Path(__file__).resolve().parent
party = Party()
enemy = None
status = "Create a party to begin."
SAVE_PATH = ROOT / "save.json"


def create_party():
    result = Party()
    for name, job, stats in (
        ("Aster", "Warrior", (60, 0, 10, 5)),
        ("Bram", "Thief", (50, 0, 8, 3)),
        ("Cleo", "White Mage", (40, 20, 4, 2)),
        ("Dane", "Black Mage", (35, 25, 3, 1)),
    ):
        character = Character(name, job, *stats)
        result.add_member(character)
    first_contract = get_quest_definition("first_contract")
    result.add_quest(Quest.from_definition(first_contract))
    world.load_map("world_map")
    return result


def party_state():
    members = [
        {
            "name": member.name,
            "job": member.job.name,
            "level": member.level,
            "hp": member.hp,
            "max_hp": member.max_hp,
            "mp": member.mp,
            "max_mp": member.max_mp,
            "gold": member.gold,
            "exp": member.exp,
        }
        for member in party.members
    ]
    enemy_state = None
    if enemy is not None:
        enemy_state = {
            "name": enemy.name,
            "hp": enemy.hp,
            "max_hp": enemy.max_hp,
        }
    return {
        "status": status,
        "members": members,
        "enemy": enemy_state,
        "map": world.current_map_name,
        "x": world.player_x,
        "y": world.player_y,
    }


class MobileHandler(BaseHTTPRequestHandler):
    def send_json(self, status_code, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            if path == "/api/state":
                self.send_json(200, party_state())
            elif path == "/api/manifest":
                self.send_json(200, {"app": "Shattered Marches Mobile"})
            else:
                self.send_json(404, {"error": "Unknown API endpoint"})
            return

        if path == "/":
            path = "/mobile.html"
        file_path = (ROOT / path.lstrip("/")).resolve()
        if ROOT not in file_path.parents and file_path != ROOT:
            self.send_error(403)
            return
        if not file_path.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self):
        path = urlparse(self.path).path
        if path == "/":
            path = "/mobile.html"
        file_path = (ROOT / path.lstrip("/")).resolve()
        if file_path.is_file():
            content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_path.stat().st_size))
            self.end_headers()
        else:
            self.send_error(404)

    def do_POST(self):
        global party, enemy, status
        path = urlparse(self.path).path
        body = self.read_json()

        if path == "/api/new":
            party = create_party()
            enemy = None
            status = "The party begins its journey."
            self.send_json(200, party_state())
            return

        if path == "/api/load":
            loaded = load_game(prompt_on_corrupt=False)
            if loaded is not None:
                party = loaded
                world.load_map("world_map")
                enemy = None
                status = "Adventure loaded."
            else:
                status = "No usable save found."
            self.send_json(200, party_state())
            return

        if path == "/api/save":
            if not party.members:
                self.send_json(400, {"error": "No party to save"})
                return
            save_game(party)
            status = "Adventure saved."
            self.send_json(200, party_state())
            return

        if path == "/api/move":
            if not party.members:
                self.send_json(400, {"error": "Create or load a party first"})
                return
            direction = body.get("direction")
            enemy = None
            if world.move_player(direction):
                if world.check_transition():
                    status = f"Entered {world.current_map_name}."
                elif random.random() < world.get_encounter_rate(world.get_current_tile()):
                    enemy = create_enemy(random.choice(
                        ("Goblin", "Wolf", "Slime", "Skeleton")
                    ))
                    status = f"{enemy.name} blocks the path!"
                else:
                    status = "The party moves forward."
            else:
                status = "The way is blocked."
            world.check_for_encounter(world.get_current_tile())
            self.send_json(200, party_state())
            return

        if path == "/api/attack":
            if enemy is None or not enemy.is_alive():
                self.send_json(400, {"error": "No active enemy"})
                return
            member = next((item for item in party.living_members()), None)
            if member is None:
                self.send_json(400, {"error": "The party is defeated"})
                return
            battle.attack(member, enemy)
            if not enemy.is_alive():
                party.update_quests("kill", enemy.name)
                status = f"{enemy.name} was defeated."
                enemy = None
            else:
                battle.attack(enemy, member)
                status = "The enemy attacks."
            self.send_json(200, party_state())
            return

        self.send_json(404, {"error": "Unknown API endpoint"})

    def log_message(self, format_string, *args):
        return


def main():
    host = "0.0.0.0"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    world.load_map("world_map")
    server = ThreadingHTTPServer((host, port), MobileHandler)
    print(f"Shattered Marches Mobile: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def start(android_storage):
    storage = Path(android_storage)
    storage.mkdir(parents=True, exist_ok=True)
    os.chdir(storage)
    main()


if __name__ == "__main__":
    main()
