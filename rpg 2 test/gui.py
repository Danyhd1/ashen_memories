import contextlib
import io
import random
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QInputDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import battle as battle_engine
import world
from arena import create_arena_boss, load_arena_challenges
from characters import Character
from enemies import create_enemy
from items import Equipment
from magic import (
    create_spell,
    get_combat_abilities,
    register_spell,
)
from jobs import BASE_CLASS_TEMPLATES
from party import Party
from quests import Quest, available_quests, show_quest_log
from races import RACES
from save import load_game, save_game
from town import buy_potion, inn
from blacksmith import (
    ARMOR_TEMPLATES,
    WEAPON_TEMPLATES,
    MATERIALS,
    craft_weapon,
    craft_armor,
)
from stronghold import STRONGHOLD_TYPES, STRONGHOLD_IMPROVEMENTS
from skills import (
    SKILL_REGISTRY,
    can_learn_skill,
    learn_skill,
    get_skill_points_per_level,
)


PROJECT_FOLDER = Path(__file__).parent
SAVE_FILE = PROJECT_FOLDER / "save.json"
STARTING_JOBS = ("Warrior", "Thief", "White Mage", "Black Mage")
STARTING_STATS = {
    "Warrior": (60, 0, 10, 5),
    "Thief": (50, 0, 8, 3),
    "White Mage": (40, 20, 4, 2),
    "Black Mage": (35, 25, 3, 1),
}


def capture_output(function, *args, **kwargs):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = function(*args, **kwargs)
    return result, output.getvalue()


def draw_pixel_sprite(painter, rect, kind, frame=0, tint=None):
    palettes = {
        "hero": ("#f4c27a", "#345b7e", "#20364e", "#e8d7ba"),
        "Warrior": ("#f2be79", "#687e9f", "#34445f", "#e9d6af"),
        "Thief": ("#f2be79", "#74537d", "#39304d", "#bddebb"),
        "White Mage": ("#f2be79", "#e6e0d1", "#738da7", "#b9e6e4"),
        "Black Mage": ("#f2be79", "#473d68", "#292743", "#d78c68"),
        "Paladin": ("#f5d08c", "#d8c993", "#66768a", "#eff1d4"),
        "Ranger": ("#f2be79", "#6d985d", "#39533e", "#e1b777"),
        "Summoner": ("#f2be79", "#987bb5", "#46375e", "#7ee0df"),
        "enemy": ("#c7d4cb", "#9d5559", "#553343", "#e3aa62"),
        "boss": ("#ead4a5", "#985c41", "#462d44", "#edb858"),
    }
    skin, tunic, shadow, accent = palettes.get(kind, palettes["hero"])
    if tint:
        tunic = tint
    unit = min(rect.width() / 8, rect.height() / 10)
    x = rect.center().x() - unit * 4
    y = rect.center().y() - unit * 5 + (1 if frame % 2 else 0)

    pixels = [
        (3, 0, 2, 2, skin),
        (2, 1, 4, 1, skin),
        (2, 2, 4, 1, shadow),
        (2, 3, 4, 2, tunic),
        (1, 3, 1, 2, accent),
        (6, 3, 1, 2, accent),
        (2, 5, 4, 1, shadow),
        (2, 6, 1, 3, tunic),
        (5, 6, 1, 3, tunic),
        (1, 9, 2, 1, shadow),
        (5, 9, 2, 1, shadow),
    ]
    if kind in ("enemy", "boss"):
        pixels.extend([
            (0, 1, 2, 1, accent),
            (6, 1, 2, 1, accent),
            (1, 2, 1, 1, "#f4e9b1"),
            (6, 2, 1, 1, "#f4e9b1"),
        ])
    for px, py, width, height, color in pixels:
        painter.fillRect(
            QRectF(x + px * unit, y + py * unit, width * unit, height * unit),
            QColor(color)
        )


class WorldCanvas(QWidget):
    def __init__(self, party, on_move, parent=None):
        super().__init__(parent)
        self.party = party
        self.on_move = on_move
        self.frame = 0
        self.setMinimumSize(570, 520)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(350)

    def _animate(self):
        self.frame += 1
        self.update()

    def paintEvent(self, event):
        if world.current_map is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#101a27"))
        tiles = world.current_map["tiles"]
        rows = len(tiles)
        columns = max(len(row) for row in tiles)
        tile_size = min(
            (self.width() - 36) / columns,
            (self.height() - 36) / rows
        )
        origin_x = (self.width() - columns * tile_size) / 2
        origin_y = (self.height() - rows * tile_size) / 2
        colors = {
            "#": "#111821",
            ".": "#55764d",
            "F": "#315d48",
            "G": "#49465a",
            "M": "#747b82",
            "W": "#376d73",
            "T": "#b99a59",
            "C": "#9e624b",
            "?": "#bd9b4b",
            "A": "#a64e50",
            "I": "#69a18b",
            "S": "#cf9c50",
            "J": "#8470ac",
            "E": "#c18b55",
            "Q": "#d3bd6b",
            "R": "#a94e50",
        }
        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                rect = QRectF(
                    origin_x + x * tile_size,
                    origin_y + y * tile_size,
                    tile_size - 2,
                    tile_size - 2
                )
                base = colors.get(tile, "#55764d")
                painter.fillRect(rect, QColor(base))
                painter.setPen(QPen(QColor("#152332"), 1))
                painter.drawRect(rect)

                inset = tile_size * 0.22
                if tile in ("F", "G", "M", "W"):
                    mark = {
                        "F": "#73a06b",
                        "G": "#8c829a",
                        "M": "#bbc1c2",
                        "W": "#6db1a8",
                    }[tile]
                    painter.fillRect(
                        QRectF(rect.x() + inset, rect.y() + inset, inset, inset),
                        QColor(mark)
                    )
                elif tile == "?":
                    painter.setPen(QPen(QColor("#fff0ae"), 2))
                    painter.drawEllipse(rect.adjusted(inset, inset, -inset, -inset))
                elif tile in ("T", "C", "A", "J", "R", "Q"):
                    painter.setPen(QPen(QColor("#fff0c5"), max(1, tile_size / 18)))
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, tile)

        player_rect = QRectF(
            origin_x + world.player_x * tile_size,
            origin_y + world.player_y * tile_size,
            tile_size - 2,
            tile_size - 2
        )
        draw_pixel_sprite(
            painter,
            player_rect.adjusted(tile_size * 0.1, tile_size * 0.05, -tile_size * 0.1, -tile_size * 0.02),
            self.party.members[0].job.name if self.party.members else "hero",
            self.frame
        )
        painter.end()

    def mousePressEvent(self, event):
        if world.current_map is None:
            return
        tiles = world.current_map["tiles"]
        rows = len(tiles)
        columns = max(len(row) for row in tiles)
        tile_size = min((self.width() - 36) / columns, (self.height() - 36) / rows)
        origin_x = (self.width() - columns * tile_size) / 2
        origin_y = (self.height() - rows * tile_size) / 2
        x = int((event.position().x() - origin_x) // tile_size)
        y = int((event.position().y() - origin_y) // tile_size)
        dx = x - world.player_x
        dy = y - world.player_y
        if abs(dx) + abs(dy) == 1:
            self.on_move({(-1, 0): "a", (1, 0): "d", (0, -1): "w", (0, 1): "s"}[(dx, dy)])


class BattleStage(QWidget):
    def __init__(self, party, enemies, parent=None):
        super().__init__(parent)
        self.party = party
        self.enemies = enemies
        self.frame = 0
        self.effects = []
        self.setMinimumSize(580, 300)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(40)

    def _animate(self):
        self.frame += 1
        alive_effects = []
        for effect in self.effects:
            effect["age"] += 1
            if effect["age"] < 36:
                alive_effects.append(effect)
        self.effects = alive_effects
        self.update()

    def impact(self, name, damage, side="enemy"):
        self.effects.append({
            "name": name,
            "damage": damage,
            "age": 0,
            "side": side,
            "x_offset": random.randint(-16, 16),
        })
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#18243a"))
        painter.fillRect(
            QRectF(0, self.height() * 0.58, self.width(), self.height() * 0.42),
            QColor("#29384a")
        )
        painter.setPen(QPen(QColor("#53677a"), 2))
        painter.drawLine(0, int(self.height() * 0.58), self.width(), int(self.height() * 0.58))

        heroes = self.party.living_members()
        enemies = [enemy for enemy in self.enemies if enemy.is_alive()]
        for index, member in enumerate(heroes):
            x = 46 + (index % 2) * 86
            y = int(self.height() * 0.3) + (index // 2) * 110
            sprite_rect = QRectF(x, y, 66, 82)
            draw_pixel_sprite(painter, sprite_rect, member.job.name, self.frame)
            self._draw_health(painter, x - 5, y + 86, member.hp, member.max_hp, 76, "#73d18c")
            painter.setPen(QColor("#e8edf4"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(x - 15, y + 100, 94, 16), Qt.AlignmentFlag.AlignCenter, member.name)

        for index, enemy in enumerate(enemies[:4]):
            x = self.width() - 150 - (index % 2) * 90
            y = int(self.height() * 0.27) + (index // 2) * 112
            sprite_rect = QRectF(x, y, 78, 90)
            draw_pixel_sprite(
                painter,
                sprite_rect,
                "boss" if enemy.max_hp > 120 else "enemy",
                self.frame
            )
            self._draw_health(painter, x - 4, y + 92, enemy.hp, enemy.max_hp, 88, "#e57373")
            painter.setPen(QColor("#f3e4d3"))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x - 28, y + 106, 112, 18),
                Qt.AlignmentFlag.AlignCenter,
                enemy.name
            )

        for effect in self.effects:
            progress = effect["age"] / 36
            alpha = max(0, int(255 * (1 - progress)))
            side_x = self.width() * (0.75 if effect["side"] == "enemy" else 0.25)
            x = side_x + effect["x_offset"]
            y = self.height() * 0.44 - progress * 70
            painter.setPen(QColor(255, 235, 148, alpha))
            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            painter.drawText(int(x), int(y), f"-{effect['damage']}")
            painter.setPen(QPen(QColor(255, 190, 92, alpha), 3))
            painter.drawEllipse(QRectF(x - 19, y - 28, 38, 38))
        painter.end()

    @staticmethod
    def _draw_health(painter, x, y, current, maximum, width, color):
        painter.fillRect(QRectF(x, y, width, 8), QColor("#101722"))
        ratio = max(0, current / maximum) if maximum else 0
        painter.fillRect(QRectF(x, y, width * ratio, 8), QColor(color))
        painter.setPen(QPen(QColor("#d9e1e9"), 1))
        painter.drawRect(QRectF(x, y, width, 8))


class BattleDialog(QDialog):
    def __init__(self, party, enemies, area, parent=None):
        super().__init__(parent)
        self.party = party
        self.enemies = list(enemies)
        self.original_enemies = list(enemies)
        self.area = area
        self.member_index = 0
        self.finished = False
        self.setWindowTitle(f"Battle - {area}")
        self.setMinimumSize(760, 680)

        layout = QVBoxLayout(self)
        self.stage = BattleStage(party, self.enemies)
        layout.addWidget(self.stage)
        self.turn_label = QLabel()
        self.turn_label.setObjectName("sectionTitle")
        layout.addWidget(self.turn_label)

        self.action_grid = QGridLayout()
        layout.addLayout(self.action_grid)
        self.action_buttons = []
        for index, (label, handler) in enumerate([
            ("Attack", self.attack_action),
            ("Skill / Spell", self.skill_action),
            ("Use Item", self.item_action),
            ("Defend", self.defend_action),
            ("Run", self.run_action),
        ]):
            button = QPushButton(label)
            button.clicked.connect(handler)
            self.action_grid.addWidget(button, index // 3, index % 3)
            self.action_buttons.append(button)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(125)
        layout.addWidget(self.log)
        self.refresh_turn()

    def living_members(self):
        return self.party.living_members()

    def active_member(self):
        members = self.living_members()
        if not members:
            return None
        if self.member_index >= len(members):
            self.member_index = 0
        return members[self.member_index]

    def refresh_turn(self):
        if self.finished:
            return
        self.enemies = battle_engine.living_enemies(self.enemies)
        if not self.living_members():
            self.finish(False)
            return
        if not self.enemies:
            self.finish(True)
            return

        member = self.active_member()
        self.turn_label.setText(
            f"{member.name}  |  {member.job.name}  |  "
            f"HP {member.hp}/{member.max_hp}  MP {member.mp}/{member.max_mp}"
        )
        self.stage.update()

    def choose_option(self, title, options):
        if not options:
            return None
        value, accepted = QInputDialog.getItem(
            self,
            title,
            "Choose a target:",
            options,
            0,
            False
        )
        return value if accepted else None

    def target_for_ability(self, ability):
        if ability.target_type == "self":
            return [self.active_member()]
        if ability.target_type == "all_allies":
            return self.living_members()
        if ability.target_type == "all_enemies":
            return self.enemies
        if ability.target_type == "ally":
            targets = self.living_members()
            selected = self.choose_option(
                ability.name,
                [f"{target.name} ({target.hp}/{target.max_hp} HP)" for target in targets]
            )
            return [targets[[f"{target.name} ({target.hp}/{target.max_hp} HP)" for target in targets].index(selected)]] if selected else []
        targets = self.enemies
        selected = self.choose_option(
            ability.name,
            [f"{target.name} ({target.hp}/{target.max_hp} HP)" for target in targets]
        )
        return [targets[[f"{target.name} ({target.hp}/{target.max_hp} HP)" for target in targets].index(selected)]] if selected else []

    def _advance_member(self):
        self.member_index += 1
        living = self.living_members()
        if self.member_index >= len(living):
            self.enemy_phase()
        else:
            self.refresh_turn()

    def _show_captured(self, function, *args, **kwargs):
        result, output = capture_output(function, *args, **kwargs)
        for line in output.splitlines():
            if line.strip():
                self.log.append(line)
        return result

    def attack_action(self):
        member = self.active_member()
        options = [f"{enemy.name} ({enemy.hp}/{enemy.max_hp} HP)" for enemy in self.enemies]
        selected = self.choose_option("Choose enemy", options)
        if selected is None:
            return
        enemy = self.enemies[options.index(selected)]
        damage = self._show_captured(battle_engine.attack, member, enemy)
        self.stage.impact(enemy.name, damage, "enemy")
        self._check_enemy_defeat(enemy)
        self._advance_member()

    def skill_action(self):
        member = self.active_member()
        abilities = get_combat_abilities(member)
        if not abilities:
            QMessageBox.information(self, "Skills", "No skills are available.")
            return
        labels = [
            f"{ability.name} (MP {ability.mp_cost}) - {ability.description}"
            for ability in abilities
        ]
        selected = self.choose_option("Choose skill", labels)
        if selected is None:
            return
        ability = abilities[labels.index(selected)]
        if member.mp < ability.mp_cost:
            QMessageBox.information(self, "Not enough MP", f"{member.name} does not have enough MP.")
            return
        targets = self.target_for_ability(ability)
        if not targets:
            return

        for index, target in enumerate(targets):
            hp_before = target.hp
            if ability.spell_type == "drain":
                member.mp -= ability.mp_cost if index == 0 else 0
                damage = random.randint(
                    max(1, int(ability.power * 0.8)),
                    max(1, int(ability.power * 1.2))
                )
                target.take_damage(damage)
                member.heal(max(1, damage // 2))
                self.log.append(f"{member.name} drains {damage} HP from {target.name}.")
            else:
                result = self._show_captured(
                    ability.cast,
                    member,
                    target,
                    charge_cost=index == 0
                )
                if not result:
                    return
            damage_done = max(0, hp_before - target.hp)
            if damage_done:
                self.stage.impact(target.name, damage_done, "ally" if target in self.party.members else "enemy")

        for enemy in list(self.enemies):
            self._check_enemy_defeat(enemy)
        self.enemies = battle_engine.living_enemies(self.enemies)
        self._advance_member()

    def item_action(self):
        member = self.active_member()
        usable_items = [
            item for item in member.inventory
            if hasattr(item, "heal_amount")
        ]
        if not usable_items:
            QMessageBox.information(self, "Items", f"{member.name} has no usable items.")
            return
        labels = [f"{item.name} - {item.description}" for item in usable_items]
        selected = self.choose_option("Choose item", labels)
        if selected is None:
            return
        item = usable_items[labels.index(selected)]
        targets = self.living_members()
        target_labels = [f"{target.name} ({target.hp}/{target.max_hp} HP)" for target in targets]
        target_choice = self.choose_option("Choose ally", target_labels)
        if target_choice is None:
            return
        target = targets[target_labels.index(target_choice)]
        self._show_captured(item.use, target)
        member.inventory.remove(item)
        self._advance_member()

    def defend_action(self):
        member = self.active_member()
        member.defending = True
        self.log.append(f"{member.name} takes a defensive stance.")
        self._advance_member()

    def run_action(self):
        result = self._show_captured(battle_engine.attempt_run, self.party)
        if result:
            self.log.append("The party escaped safely.")
            self.finish(False)
        else:
            self._advance_member()

    def _check_enemy_defeat(self, enemy):
        if enemy.hp <= 0:
            self._show_captured(self.party.update_quests, "kill", enemy.name)
            self.log.append(f"{enemy.name} is defeated!")

    def enemy_phase(self):
        self.member_index = 0
        if not self.enemies:
            self.refresh_turn()
            return

        participants = self.party.members + self.enemies
        before_effects = {
            combatant: combatant.hp
            for combatant in participants
        }
        self._show_captured(battle_engine.apply_round_effects, participants)
        self._animate_hp_changes(before_effects)
        self.enemies = battle_engine.living_enemies(self.enemies)
        if self.enemies and self.living_members():
            before_attacks = {
                member: member.hp
                for member in self.living_members()
            }
            self._show_captured(battle_engine.enemy_turn, self.party, self.enemies)
            self._animate_hp_changes(before_attacks, side="ally")

        for member in self.party.members:
            member.defending = False
        self._show_captured(battle_engine.reduce_status_durations, participants)
        self.stage.update()
        self.refresh_turn()

    def _animate_hp_changes(self, hp_before, side=None):
        for combatant, old_hp in hp_before.items():
            damage = max(0, old_hp - combatant.hp)
            if damage:
                target_side = side
                if target_side is None:
                    target_side = (
                        "ally"
                        if combatant in self.party.members
                        else "enemy"
                    )
                self.stage.impact(combatant.name, damage, target_side)

    def finish(self, victory):
        if self.finished:
            return
        self.finished = True
        if victory:
            defeated = [
                enemy for enemy in self.original_enemies
                if not enemy.is_alive()
            ]
            self._show_captured(battle_engine.give_rewards, self.party, defeated)
            for enemy in defeated:
                self._show_captured(self.party.update_quests, "kill", enemy.name)
                for drop in enemy.drops:
                    if random.random() < drop.get("chance", 1.0):
                        self._show_captured(
                            self.party.update_quests,
                            "collect",
                            drop["item"]
                        )
            self.log.append("Victory!")
            self.accept()
        else:
            for member in self.party.members:
                member.defending = False
            self.log.append("Battle ended.")
            self.reject()


class NewGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Your Party")
        self.setMinimumWidth(680)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Choose a name, race, starting job, and class options for each adventurer."
        ))
        form = QFormLayout()
        self.name_fields = []
        self.job_fields = []
        self.race_fields = []
        self.custom_name_fields = []
        self.custom_stats = []
        self.ability_fields = []
        self.point_budget_labels = []
        point_budget = 30
        for index in range(4):
            name = QComboBox()
            name.setEditable(True)
            name.addItems(["Aster", "Bram", "Cleo", "Dane"])
            name.setCurrentIndex(index)
            job = QComboBox()
            job.addItems((
                *STARTING_JOBS,
                *BASE_CLASS_TEMPLATES,
                "Custom"
            ))
            job.setCurrentIndex(index)

            race = QComboBox()
            race.addItems(RACES)
            race.setToolTip("\n".join(
                f"{race_name}: {race_data['description']}"
                for race_name, race_data in RACES.items()
            ))

            custom_name = QComboBox()
            custom_name.setEditable(True)
            custom_name.addItem(f"Custom Class {index + 1}")
            custom_name.setEnabled(False)

            stat_fields = {}
            stat_row = QHBoxLayout()
            for label, key, minimum in (
                ("HP", "max_hp", 35),
                ("MP", "max_mp", 0),
                ("STR", "strength", 1),
                ("DEF", "defense", 1),
            ):
                stat = QSpinBox()
                stat.setRange(minimum, 100)
                stat.setValue(STARTING_STATS[STARTING_JOBS[index]][
                    ("max_hp", "max_mp", "strength", "defense").index(key)
                ])
                stat_fields[key] = stat
                stat_row.addWidget(QLabel(label))
                stat_row.addWidget(stat)
                stat.valueChanged.connect(lambda *_args, i=index: self.update_point_budget(i))

            abilities = QComboBox()
            abilities.addItems(sorted({
                "Power Strike", "Guard Stance", "Backstab", "First Aid",
                "Protect", "Fire", "Cure", "Aimed Shot", "Holy Strike"
            }))

            job.currentTextChanged.connect(
                lambda text, field=custom_name: field.setEnabled(text == "Custom")
            )
            job.currentTextChanged.connect(
                lambda *_args, i=index: self.update_point_budget(i)
            )
            budget_label = QLabel("Custom class budget: 30 remaining")
            budget_label.setVisible(False)
            self.point_budget_labels.append(budget_label)
            self.name_fields.append(name)
            self.job_fields.append(job)
            self.race_fields.append(race)
            self.custom_name_fields.append(custom_name)
            self.custom_stats.append(stat_fields)
            self.ability_fields.append(abilities)
            form.addRow(f"Character {index + 1} name", name)
            form.addRow("Starting job", job)
            form.addRow("Race", race)
            form.addRow("Custom class name", custom_name)
            form.addRow("Point-buy characteristics", stat_row)
            form.addRow("Point budget", budget_label)
            form.addRow("Starting ability", abilities)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def update_point_budget(self, index):
        stats = self.custom_stats[index]
        is_custom = self.job_fields[index].currentText() == "Custom"
        label = self.point_budget_labels[index]
        label.setVisible(is_custom)
        if not is_custom:
            return

        spent = (
            max(0, stats["max_hp"].value() - 35) // 2
            + max(0, stats["max_mp"].value())
            + max(0, stats["strength"].value() - 1) * 2
            + max(0, stats["defense"].value() - 1) * 2
        )
        remaining = 30 - spent
        label.setText(f"Custom class budget: {remaining} remaining")
        label.setStyleSheet("color: #d7b87c;" if remaining >= 0 else "color: #ff7b72;")

    def accept(self):
        for index, job_field in enumerate(self.job_fields):
            if job_field.currentText() != "Custom":
                continue
            stats = self.custom_stats[index]
            spent = (
                max(0, stats["max_hp"].value() - 35) // 2
                + max(0, stats["max_mp"].value())
                + max(0, stats["strength"].value() - 1) * 2
                + max(0, stats["defense"].value() - 1) * 2
            )
            if spent > 30:
                QMessageBox.warning(
                    self,
                    "Point Budget Exceeded",
                    f"Character {index + 1} exceeds the 30-point custom class budget."
                )
                return
        super().accept()

    def build_party(self):
        party = Party()
        for index, (name_field, job_field) in enumerate(zip(
            self.name_fields,
            self.job_fields
        )):
            name = name_field.currentText().strip()
            if not name:
                name = job_field.currentText()
            job = job_field.currentText()
            race = self.race_fields[index].currentText()
            stat_fields = self.custom_stats[index]
            stats = (
                stat_fields["max_hp"].value(),
                stat_fields["max_mp"].value(),
                stat_fields["strength"].value(),
                stat_fields["defense"].value()
            )
            ability = self.ability_fields[index].currentText()
            custom_name = self.custom_name_fields[index].currentText().strip()
            custom_name = custom_name or f"Custom Class {index + 1}"
            custom_job = custom_name if job == "Custom" else None
            template = job if job in BASE_CLASS_TEMPLATES else None
            magic_type = (
                BASE_CLASS_TEMPLATES[job]["magic_type"]
                if template
                else ("none" if job in STARTING_JOBS else "medium")
            )
            if template:
                stats = BASE_CLASS_TEMPLATES[job]["stats"]
            character = Character(
                name,
                job,
                *stats,
                race=race,
                custom_job=custom_job,
                abilities=[ability],
                magic_type=magic_type,
                template=template
            )
            if template:
                for template_ability in BASE_CLASS_TEMPLATES[job]["abilities"]:
                    template_spell = create_spell(template_ability)
                    if template_spell and template_spell.name not in {
                        spell.name for spell in character.spells
                    }:
                        character.spells.append(template_spell)
            elif job == "White Mage" or ability == "Cure":
                character.spells.append(create_spell("Cure"))
            elif job == "Black Mage" or ability == "Fire":
                character.spells.append(create_spell("Fire"))
            elif ability and ability not in {spell.name for spell in character.spells}:
                selected = create_spell(ability)
                if selected:
                    character.spells.append(selected)
            party.add_member(character)
        first_contract = Quest.from_definition(
            __import__("quests").get_quest_definition("first_contract")
        )
        party.add_quest(first_contract)
        return party


class GameWindow(QMainWindow):
    def __init__(self, party, parent=None):
        super().__init__(parent)
        self.party = party
        self.setWindowTitle("Shattered Marches")
        self.resize(1120, 760)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        title_row = QHBoxLayout()
        self.location_title = QLabel()
        self.location_title.setObjectName("gameTitle")
        title_row.addWidget(self.location_title)
        title_row.addStretch()
        self.gold_label = QLabel()
        title_row.addWidget(self.gold_label)
        root.addLayout(title_row)

        body = QHBoxLayout()
        root.addLayout(body, 1)
        self.map_canvas = WorldCanvas(party, self.move_player)
        body.addWidget(self.map_canvas, 3)

        side = QVBoxLayout()
        body.addLayout(side, 2)
        party_box = QGroupBox("Party")
        party_layout = QVBoxLayout(party_box)
        self.party_labels = []
        for _ in party.members:
            label = QLabel()
            label.setWordWrap(True)
            party_layout.addWidget(label)
            self.party_labels.append(label)
        side.addWidget(party_box)

        quest_box = QGroupBox("Active objectives")
        quest_layout = QVBoxLayout(quest_box)
        self.quest_label = QLabel()
        self.quest_label.setWordWrap(True)
        quest_layout.addWidget(self.quest_label)
        side.addWidget(quest_box)

        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setPlaceholderText("Your journey's events appear here.")
        self.event_log.setMaximumHeight(140)
        side.addWidget(self.event_log)

        controls = QGridLayout()
        root.addLayout(controls)
        actions = [
            ("Quest Board", self.show_board),
            ("Quest Log", self.show_quests),
            ("Party", self.show_party),
            ("Inventory", self.show_inventory),
            ("Stronghold", self.show_stronghold),
            ("Skills", self.show_skills),
            ("Save", self.save),
        ]
        for index, (label, callback) in enumerate(actions):
            button = QPushButton(label)
            button.clicked.connect(callback)
            controls.addWidget(button, index // 4, index % 4)

        world.load_map("world_map")
        self.refresh_ui()
        self.statusBar().showMessage(
            "Move with WASD or arrow keys. You can also click an adjacent map tile."
        )

    def keyPressEvent(self, event: QKeyEvent):
        directions = {
            Qt.Key.Key_W: "w",
            Qt.Key.Key_Up: "w",
            Qt.Key.Key_S: "s",
            Qt.Key.Key_Down: "s",
            Qt.Key.Key_A: "a",
            Qt.Key.Key_Left: "a",
            Qt.Key.Key_D: "d",
            Qt.Key.Key_Right: "d",
        }
        direction = directions.get(event.key())
        if direction:
            self.move_player(direction)
            return
        super().keyPressEvent(event)

    def refresh_ui(self):
        if world.current_map:
            self.location_title.setText(world.current_map["name"])
        leader = self.party.members[0] if self.party.members else None
        self.gold_label.setText(f"Gold: {leader.gold if leader else 0}")
        for index, member in enumerate(self.party.members):
            self.party_labels[index].setText(
                f"<b>{member.name}</b> — {member.job.name} (Lv {member.level})<br>"
                f"HP {member.hp}/{member.max_hp} &nbsp; MP {member.mp}/{member.max_mp}<br>"
                f"STR {member.strength} &nbsp; DEF {member.defense}"
            )
        active_quests = [quest for quest in self.party.quests if not quest.completed]
        if active_quests:
            self.quest_label.setText("<br>".join(
                f"• {quest.name}: {quest.progress}/{quest.goal}"
                for quest in active_quests
            ))
        else:
            self.quest_label.setText("No active quests.")
        self.map_canvas.update()

    def log(self, message):
        if message:
            self.event_log.append(message)
        self.refresh_ui()

    def move_player(self, direction):
        moved, output = capture_output(world.move_player, direction)
        if not moved:
            self.log(output.strip())
            return

        transitioned, _ = capture_output(world.check_transition)
        if transitioned:
            self.log(f"Entered {world.current_map['name']}.")
            _, quest_output = capture_output(world.record_location, self.party)
            self.log(quest_output.strip())
            event_handled = self.resolve_location_event()
            self.map_canvas.update()
            if not event_handled:
                self.handle_current_tile()
            self.refresh_ui()
            return

        _, quest_output = capture_output(world.record_location, self.party)
        self.log(quest_output.strip())
        if self.resolve_location_event():
            return

        tile = world.get_current_tile()
        if world.check_for_encounter(tile):
            area = world.get_area_name(tile)
            enemies = battle_engine.create_enemy_group(area, self.party)
            self.start_battle(enemies, area)
        else:
            self.handle_current_tile()
        self.map_canvas.update()
        self.refresh_ui()

    def resolve_location_event(self):
        event_id, event = world.get_location_event()
        if not event or event_id in self.party.discovered_events:
            return False

        if event["type"] == "battle":
            enemy = create_enemy(event["enemy"])
            if enemy is None:
                QMessageBox.warning(self, "Location event", "The event's enemy data is missing.")
                return True
            QMessageBox.information(self, event["name"], event["text"])
            victory = self.start_battle(
                [enemy],
                world.get_area_name(world.get_current_tile())
            )
            if victory:
                self.party.discovered_events.append(event_id)
            return True

        _, output = capture_output(world.handle_location_event, self.party)
        QMessageBox.information(self, event["name"], event["text"])
        self.log(output.strip())
        return True

    def handle_current_tile(self):
        tile = world.get_current_tile()
        map_name = world.current_map_name
        if map_name == "town_map":
            if tile == "I":
                self.open_inn()
            elif tile == "S":
                self.open_shop()
            elif tile == "J":
                self.open_guild()
        elif map_name == "castle_map" and tile == "Q":
            self.show_board()
        elif map_name == "arena_map" and tile == "R":
            self.start_arena()

    def start_battle(self, enemies, area):
        if not enemies:
            return False
        dialog = BattleDialog(self.party, enemies, area, self)
        victory = dialog.exec() == QDialog.DialogCode.Accepted
        self.log(dialog.log.toPlainText())
        self.refresh_ui()
        return victory

    def show_board(self):
        available = available_quests(self.party)
        if not available:
            QMessageBox.information(self, "Quest Board", "No new contracts are available.")
            return
        options = [
            f"{quest['name']} [{quest['type'].title()}] — {quest['description']}"
            for quest in available
        ]
        selected = QInputDialog.getItem(
            self,
            "Castle Quest Board",
            "Accept a contract:",
            options,
            0,
            False
        )
        if not selected[1]:
            return
        quest = Quest.from_definition(available[options.index(selected[0])])
        self.party.add_quest(quest)
        self.log(f"Accepted quest: {quest.name}")

    def show_quests(self):
        _, output = capture_output(show_quest_log, self.party)
        QMessageBox.information(self, "Quest Log", output)

    def show_party(self):
        lines = []
        for member in self.party.members:
            lines.append(
                f"{member.name} — {member.job.name}, level {member.level}\n"
                f"HP {member.hp}/{member.max_hp} | MP {member.mp}/{member.max_mp}\n"
                f"Strength {member.strength} | Defense {member.defense} | EXP {member.exp}\n"
                f"Weapon: {member.weapon.name if member.weapon else 'None'} | "
                f"Armor: {member.armor.name if member.armor else 'None'}"
            )
        QMessageBox.information(self, "Party", "\n\n".join(lines))

    def show_stronghold(self):
        stronghold = self.party.stronghold
        dialog = QDialog(self)
        dialog.setWindowTitle("Stronghold")
        dialog.setMinimumWidth(620)
        layout = QVBoxLayout(dialog)

        name_field = QComboBox()
        name_field.setEditable(True)
        name_field.setEditText(stronghold.name)
        layout.addWidget(QLabel("Stronghold name"))
        layout.addWidget(name_field)

        type_field = QComboBox()
        type_field.addItems(STRONGHOLD_TYPES)
        type_field.setCurrentText(stronghold.stronghold_type)
        layout.addWidget(QLabel("Stronghold type"))
        layout.addWidget(type_field)

        improvement_field = QComboBox()
        improvement_field.setMinimumWidth(520)
        layout.addWidget(QLabel("Available improvements"))
        layout.addWidget(improvement_field)

        bonus_label = QLabel()
        bonus_label.setWordWrap(True)
        layout.addWidget(bonus_label)

        def refresh_improvements():
            improvement_field.clear()
            available = [
                item
                for item in STRONGHOLD_IMPROVEMENTS
                if stronghold.can_install(item)
            ]
            for item in available:
                improvement_field.addItem(
                    f"{item.name} [{item.category}] - {item.cost} gold",
                    item.id
                )
            bonus_label.setText(
                "Bonuses: " + ", ".join(
                    f"{name} +{value}"
                    for name, value in stronghold.bonuses.items()
                    if value
                ) or "No bonuses installed."
            )

        def refresh_type():
            stronghold.stronghold_type = type_field.currentText()
            stronghold.name = name_field.currentText().strip() or stronghold.name
            refresh_improvements()

        type_field.currentTextChanged.connect(lambda _text: refresh_type())
        name_field.currentTextChanged.connect(
            lambda _text: setattr(stronghold, "name", name_field.currentText().strip() or stronghold.name)
        )
        refresh_improvements()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Close
        )
        layout.addWidget(buttons)

        def apply_improvement():
            improvement_id = improvement_field.currentData()
            if not improvement_id:
                return
            improvement = stronghold.get_improvement(improvement_id)
            leader = self.party.members[0]
            installed = stronghold.install(improvement_id, leader.gold)
            if installed is None:
                QMessageBox.warning(
                    dialog,
                    "Cannot Install",
                    "You lack the gold or prerequisites for this improvement."
                )
                return
            leader.gold -= improvement.cost
            self.gold_label.setText(f"Gold: {leader.gold}")
            refresh_improvements()

        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(apply_improvement)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()

    def show_skills(self):
        if not self.party.members:
            return
        member = self.party.members[0]
        dialog = QDialog(self)
        dialog.setWindowTitle("Skill Trees")
        dialog.setMinimumWidth(620)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            f"{member.name} - Level {member.level} - "
            f"Skill points: {member.skill_points}"
        ))

        skill_combo = QComboBox()
        available = [
            skill for skill in SKILL_REGISTRY.values()
            if can_learn_skill(member, skill)
        ]
        for skill in available:
            skill_combo.addItem(
                f"{skill.name} [{skill.category}] - "
                f"{skill.cost} point(s) - Level {skill.unlock_level}",
                skill.id
            )
        if not available:
            skill_combo.addItem("No skills currently available")
        layout.addWidget(skill_combo)

        detail = QLabel()
        detail.setWordWrap(True)
        layout.addWidget(detail)

        def update_detail():
            skill_id = skill_combo.currentData()
            skill = SKILL_REGISTRY.get(skill_id)
            if skill is None:
                detail.setText("Unlock skills at the required level and with prerequisites.")
                return
            prerequisites = ", ".join(skill.prerequisites) or "None"
            detail.setText(
                f"{skill.description}\n"
                f"Prerequisites: {prerequisites}\n"
                f"Unlock level: {skill.unlock_level}"
            )

        skill_combo.currentIndexChanged.connect(lambda _index: update_detail())
        update_detail()
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Close
        )
        layout.addWidget(buttons)

        def buy_skill():
            skill_id = skill_combo.currentData()
            if not skill_id:
                return
            skill = learn_skill(member, skill_id)
            if skill is None:
                QMessageBox.warning(dialog, "Cannot Learn", "This skill is unavailable.")
                return
            self.log(
                f"{member.name} learned {skill.name}. "
                f"Skill points left: {member.skill_points}"
            )
            dialog.accept()

        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(buy_skill)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()
        self.refresh_ui()

    def show_inventory(self):
        if not self.party.members:
            return
        leader = self.party.members[0]
        if not leader.inventory:
            QMessageBox.information(self, "Inventory", "The party inventory is empty.")
            return
        lines = [
            f"{item.name}: {item.description}"
            for item in leader.inventory
        ]
        QMessageBox.information(
            self,
            f"{leader.name}'s Inventory",
            "\n".join(lines)
        )

    def open_inn(self):
        leader = self.party.members[0]
        answer = QMessageBox.question(
            self,
            "Town Inn",
            f"Rest and fully restore the party for 20 gold? (You have {leader.gold}.)"
        )
        if answer == QMessageBox.StandardButton.Yes:
            _, output = capture_output(inn, self.party)
            self.log(output.strip() or "The party rests at the inn.")

    def open_shop(self):
        leader = self.party.members[0]
        answer = QMessageBox.question(
            self,
            "Town Shop",
            f"Buy a Potion for 50 gold? (You have {leader.gold}.)"
        )
        if answer == QMessageBox.StandardButton.Yes:
            _, output = capture_output(buy_potion, self.party)
            self.log(output.strip())

    def open_guild(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Guild of Masters")
        layout = QVBoxLayout(dialog)
        member_combo = QComboBox()
        for member in self.party.members:
            member_combo.addItem(member.name, member)
        layout.addWidget(QLabel("Character"))
        layout.addWidget(member_combo)
        job_combo = QComboBox()
        for job in sorted(self.party.unlocked_jobs):
            job_combo.addItem(job)
        layout.addWidget(QLabel("Choose an unlocked job"))
        layout.addWidget(job_combo)

        equipment_combo = QComboBox()
        equipment = []
        for item in member_combo.currentData().inventory:
            if isinstance(item, Equipment):
                equipment.append(item)
        equipment_combo.addItem("Do not equip anything", None)
        for item in equipment:
            equipment_combo.addItem(f"{item.name} ({item.slot})", item)
        layout.addWidget(QLabel("Equipment (optional)"))
        layout.addWidget(equipment_combo)

        def update_equipment():
            equipment_combo.clear()
            equipment_combo.addItem("Do not equip anything", None)
            member = member_combo.currentData()
            for item in member.inventory:
                if isinstance(item, Equipment):
                    equipment_combo.addItem(f"{item.name} ({item.slot})", item)

        member_combo.currentIndexChanged.connect(
            lambda _index: update_equipment()
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Close
        )
        layout.addWidget(buttons)

        def apply_changes():
            member = member_combo.currentData()
            new_job = job_combo.currentText()
            if new_job != member.job.name:
                member.job = __import__("jobs").create_job(new_job)
                minimum_mp = {"Paladin": 8, "Ranger": 6, "Summoner": 20}.get(new_job, 0)
                if member.max_mp < minimum_mp:
                    member.max_mp = minimum_mp
                    member.mp = minimum_mp
                self.log(f"{member.name} changed jobs to {new_job}.")
            item = equipment_combo.currentData()
            if item is not None:
                member.equip(item)
                self.log(f"{member.name} equipped {item.name}.")

        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(apply_changes)

        craft_button = buttons.addButton(
            "Visit Blacksmith",
            QDialogButtonBox.ButtonRole.ActionRole
        )

        def open_blacksmith():
            member = member_combo.currentData()
            self.open_blacksmith(member)

        craft_button.clicked.connect(open_blacksmith)
        buttons.rejected.connect(dialog.reject)
        buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(dialog.accept)
        dialog.exec()
        self.refresh_ui()

    def open_blacksmith(self, member):
        dialog = QDialog(self)
        dialog.setWindowTitle("Guild Blacksmith")
        dialog.setMinimumWidth(440)
        layout = QFormLayout(dialog)

        name_field = QComboBox()
        name_field.setEditable(True)
        name_field.setEditText("Named Weapon")

        category_field = QComboBox()
        category_field.addItems(("Weapon", "Armor"))

        type_field = QComboBox()
        type_field.addItems(WEAPON_TEMPLATES)

        material_field = QComboBox()
        material_field.addItems(MATERIALS)

        preview = QLabel("")
        layout.addRow("Item name", name_field)
        layout.addRow("Category", category_field)
        layout.addRow("Type", type_field)
        layout.addRow("Material", material_field)
        layout.addRow("Preview", preview)

        def update_type():
            type_field.clear()
            if category_field.currentText() == "Weapon":
                type_field.addItems(WEAPON_TEMPLATES)
            else:
                type_field.addItems(ARMOR_TEMPLATES)

        def update_preview():
            if category_field.currentText() == "Weapon":
                item = craft_weapon(
                    name_field.currentText().strip() or "Named Weapon",
                    type_field.currentText(),
                    material_field.currentText(),
                    member.level
                )
            else:
                item = craft_armor(
                    name_field.currentText().strip() or "Named Armor",
                    type_field.currentText(),
                    material_field.currentText(),
                    member.level
                )
            preview.setText(
                f"{item.description}\nCost: {item.value} gold\n"
                f"+{item.strength_bonus} STR / +{item.defense_bonus} DEF / "
                f"+{item.max_hp_bonus} HP / +{item.max_mp_bonus} MP"
            )

        category_field.currentTextChanged.connect(update_type)
        category_field.currentTextChanged.connect(lambda _text: update_preview())
        type_field.currentTextChanged.connect(lambda _text: update_preview())
        material_field.currentTextChanged.connect(lambda _text: update_preview())
        name_field.currentTextChanged.connect(lambda _text: update_preview())
        update_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(buttons)

        def craft():
            if category_field.currentText() == "Weapon":
                item = craft_weapon(
                    name_field.currentText().strip() or "Named Weapon",
                    type_field.currentText(),
                    material_field.currentText(),
                    member.level
                )
            else:
                item = craft_armor(
                    name_field.currentText().strip() or "Named Armor",
                    type_field.currentText(),
                    material_field.currentText(),
                    member.level
                )
            if member.gold < item.value:
                QMessageBox.warning(
                    dialog,
                    "Not Enough Gold",
                    f"{item.name} costs {item.value} gold."
                )
                return
            member.gold -= item.value
            member.inventory.append(item)
            self.log(f"{member.name} crafted {item.name} for {item.value} gold.")
            dialog.accept()

        buttons.accepted.connect(craft)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()
        self.refresh_ui()

    def start_arena(self):
        challenges = load_arena_challenges()
        next_index = len(self.party.arena_wins)
        if next_index >= len(challenges):
            QMessageBox.information(self, "Arena", "Your party has completed the championship circuit.")
            return
        challenge = challenges[next_index]
        quest_id = f"arena_{challenge['id']}"
        quest = next(
            (
                item for item in self.party.quests
                if item.quest_id == quest_id and not item.completed
            ),
            None
        )
        if quest is None:
            QMessageBox.information(
                self,
                "Arena Steward",
                "Accept the matching trial contract at the castle quest board first."
            )
            return

        answer = QMessageBox.question(
            self,
            challenge["name"],
            f"{challenge['description']}\n\nEnter the arena bout?"
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        victory = self.start_battle([create_arena_boss(challenge)], "Arena")
        if victory:
            self.party.arena_wins.append(challenge["id"])
            _, output = capture_output(
                self.party.update_quests,
                "arena_win",
                challenge["name"]
            )
            self.log(output.strip())

    def save(self):
        try:
            _, output = capture_output(
                save_game,
                self.party,
                path=SAVE_FILE
            )
        except OSError as error:
            QMessageBox.critical(self, "Save failed", str(error))
            return
        self.log(output.strip() or "Game saved.")
        self.statusBar().showMessage(f"Game saved to {SAVE_FILE}", 5000)


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shattered Marches")
        self.resize(560, 430)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading = QLabel("SHATTERED\nMARCHES")
        heading.setObjectName("titleCard")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        subtitle = QLabel("A pixel-art party RPG")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        new_button = QPushButton("New Adventure")
        load_button = QPushButton("Load Adventure")
        quit_button = QPushButton("Quit")
        for button in (new_button, load_button, quit_button):
            button.setMinimumHeight(44)
            layout.addWidget(button)
        new_button.clicked.connect(self.new_game)
        load_button.clicked.connect(self.load)
        quit_button.clicked.connect(self.close)
        self.game_window = None

    def new_game(self):
        dialog = NewGameDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.launch_game(dialog.build_party())

    def load(self):
        try:
            party, output = capture_output(
                load_game,
                path=SAVE_FILE,
                prompt_on_corrupt=False
            )
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Load failed", str(error))
            return
        if party is None:
            QMessageBox.information(
                self,
                "Load Adventure",
                output.strip() or "No usable save was found."
            )
            return
        self.launch_game(party)

    def launch_game(self, party):
        self.game_window = GameWindow(party)
        self.game_window.show()
        self.hide()
        self.game_window.destroyed.connect(self.show)


STYLESHEET = """
QWidget {
    background: #182333;
    color: #e6e3d9;
    font-family: "Segoe UI";
    font-size: 13px;
}
QMainWindow, QDialog {
    background: #182333;
}
QLabel#titleCard {
    color: #f0c575;
    font-family: "Georgia";
    font-size: 38px;
    font-weight: bold;
}
QLabel#gameTitle {
    color: #f0c575;
    font-family: "Georgia";
    font-size: 24px;
    font-weight: bold;
}
QLabel#sectionTitle {
    color: #edc778;
    font-size: 16px;
    font-weight: bold;
}
QPushButton {
    background: #354a60;
    border: 1px solid #657c91;
    border-radius: 5px;
    padding: 8px 12px;
    color: #f4ead5;
}
QPushButton:hover {
    background: #4b6680;
    border-color: #e0bd71;
}
QPushButton:pressed {
    background: #8c5b4b;
}
QGroupBox {
    border: 1px solid #536477;
    border-radius: 6px;
    margin-top: 10px;
    padding: 9px;
    color: #e8c77f;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
}
QTextEdit, QComboBox {
    background: #101924;
    border: 1px solid #3d5063;
    border-radius: 4px;
    padding: 5px;
}
QStatusBar {
    color: #bdc8d2;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    launcher = LauncherWindow()
    launcher.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
