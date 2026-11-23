import random

from enemies import create_enemy
from leveling import gain_exp
from magic import get_combat_abilities


def get_possible_enemies(area):
    enemy_tables = {
        "Grassland": ["Goblin", "Bandit", "Slime"],
        "Forest": ["Goblin", "Wolf", "Snake", "Bandit"],
        "Graveyard": ["Skeleton", "Zombie", "Wraith", "Shaman"],
        "Mountain": ["Ogre", "Harpy", "Wyvern"],
        "Wetlands": ["Snake", "Zombie", "Slime"],
        "Castle": ["Skeleton", "Wraith", "Shaman", "Dark Knight"],
        "Town": ["Goblin", "Bandit"]
    }
    return enemy_tables.get(area, ["Goblin"])


def create_enemy_group(area, party=None):
    enemy_count = random.randint(1, 3)
    possible_enemies = get_possible_enemies(area)
    enemies = []

    for _ in range(enemy_count):
        enemy = create_enemy(random.choice(possible_enemies))
        if enemy is not None:
            enemies.append(enemy)

    if not enemies:
        print("\nNo valid enemies found for this area.")
        fallback_enemy = create_enemy("Goblin")
        if fallback_enemy is not None:
            enemies.append(fallback_enemy)

    if area == "Castle" and party is not None and any(
        quest.objective_type == "bounty"
        and quest.target == "Dread Captain"
        and not quest.completed
        for quest in party.quests
    ):
        if not any(enemy.name == "Dread Captain" for enemy in enemies):
            captain = create_enemy("Dread Captain")
            if captain is not None:
                enemies.append(captain)

    return enemies


def living_enemies(enemies):
    return [enemy for enemy in enemies if enemy.is_alive()]


def attack(attacker, defender, multiplier=1.0, ignore_defense=False):
    if attacker is None or defender is None or not defender.is_alive():
        return 0

    strength = getattr(attacker, "strength", 0)
    if attacker.has_status("empowered"):
        strength = int(strength * 1.25)

    defense = getattr(defender, "defense", 0)
    if defender.has_status("exposed"):
        defense = max(0, defense - 3)
    if ignore_defense:
        defense = 0

    damage = max(1, int((strength - defense) * multiplier))
    if defender.defending:
        damage = max(1, damage // 2)
    elif defender.has_status("protected") or defender.has_status("guarded"):
        damage = max(1, int(damage * 0.75))

    defender.take_damage(damage)
    print(f"{attacker.name} deals {damage} damage to {defender.name}.")
    if not defender.is_alive():
        print(f"{defender.name} has fallen.")
    return damage


def show_status(party, enemies):
    print("\n===== PARTY =====")
    for member in party.members:
        status = "Down" if not member.is_alive() else "Ready"
        effects = ", ".join(
            effect.replace("_", " ")
            for effect in member.status_effects
            if member.has_status(effect)
        )
        effect_text = f" | {effects}" if effects else ""
        print(
            f"{member.name} HP: {member.hp}/{member.max_hp} "
            f"MP: {member.mp}/{member.max_mp} [{status}]{effect_text}"
        )

    print("\n===== ENEMIES =====")
    for index, enemy in enumerate(enemies, start=1):
        effects = ", ".join(
            effect.replace("_", " ")
            for effect in enemy.status_effects
            if enemy.has_status(effect)
        )
        effect_text = f" | {effects}" if effects else ""
        print(f"{index}. {enemy.name} HP: {enemy.hp}/{enemy.max_hp}{effect_text}")


def choose_target(targets, prompt, show_hp=False):
    targets = [target for target in targets if target.is_alive()]
    if not targets:
        return None

    while True:
        print(f"\n{prompt}")
        for index, target in enumerate(targets, start=1):
            health = f" HP: {target.hp}/{target.max_hp}" if show_hp else ""
            print(f"{index}. {target.name}{health}")

        try:
            choice = int(input("> "))
            if 1 <= choice <= len(targets):
                return targets[choice - 1]
        except ValueError:
            pass
        print("Invalid target.")


def choose_enemy_target(enemies):
    return choose_target(living_enemies(enemies), "Choose enemy target:")


def choose_party_target(party):
    return choose_target(party.living_members(), "Choose party target:", show_hp=True)


def choose_ability(member):
    abilities = get_combat_abilities(member)
    if not abilities:
        print("\nNo skills available.")
        return None

    while True:
        print("\nChoose skill:")
        for index, ability in enumerate(abilities, start=1):
            print(
                f"{index}. {ability.name} "
                f"(MP {ability.mp_cost}) - {ability.description}"
            )
        print("0. Cancel")

        try:
            choice = int(input("> "))
            if choice == 0:
                return None
            if 1 <= choice <= len(abilities):
                return abilities[choice - 1]
        except ValueError:
            pass
        print("Invalid skill.")


def choose_item(member):
    if not member.inventory:
        print("\nNo items available.")
        return None

    while True:
        print("\nChoose item:")
        for index, item in enumerate(member.inventory, start=1):
            print(f"{index}. {item.name} - {item.description}")
        print("0. Cancel")

        try:
            choice = int(input("> "))
            if choice == 0:
                return None
            if 1 <= choice <= len(member.inventory):
                return member.inventory[choice - 1]
        except ValueError:
            pass
        print("Invalid item.")


def use_inventory_item(party, member):
    item = choose_item(member)
    if item is None:
        return False

    if not hasattr(item, "heal_amount"):
        print("\nThat item cannot be used in battle.")
        return False

    target = choose_party_target(party)
    if target is None:
        return False

    item.use(target)
    member.inventory.remove(item)
    return True


def _targets_for_ability(ability, party, enemies, caster):
    if ability.target_type == "self":
        return [caster]
    if ability.target_type == "ally":
        target = choose_party_target(party)
        return [target] if target is not None else []
    if ability.target_type == "all_allies":
        return party.living_members()
    if ability.target_type == "all_enemies":
        return living_enemies(enemies)

    target = choose_enemy_target(enemies)
    return [target] if target is not None else []


def handle_ability(member, party, enemies):
    ability = choose_ability(member)
    if ability is None:
        return False

    targets = _targets_for_ability(ability, party, enemies, member)
    if not targets:
        print("There are no valid targets.")
        return False

    if member.mp < ability.mp_cost:
        print(f"{member.name} does not have enough MP.")
        return False

    for index, target in enumerate(targets):
        if ability.spell_type == "drain":
            if index == 0:
                member.mp -= ability.mp_cost
            damage = random.randint(
                max(1, int(ability.power * 0.8)),
                max(1, int(ability.power * 1.2))
            )
            target.take_damage(damage)
            healing = max(1, damage // 2)
            member.heal(healing)
            print(
                f"{member.name} drains {damage} HP from {target.name} "
                f"and recovers {healing} HP."
            )
            continue

        if not ability.cast(member, target, charge_cost=index == 0):
            return False

    for enemy in list(enemies):
        if not enemy.is_alive():
            party.update_quests("kill", enemy.name)

    enemies[:] = living_enemies(enemies)
    return True


def handle_attack(member, enemies, party):
    target = choose_enemy_target(enemies)
    if target is None:
        return False

    attack(member, target)
    if not target.is_alive():
        party.update_quests("kill", target.name)
        enemies.remove(target)
    return True


def apply_round_effects(combatants):
    for combatant in combatants:
        if not combatant.is_alive():
            continue
        if combatant.has_status("poison"):
            damage = max(1, combatant.max_hp // 12)
            combatant.take_damage(damage)
            print(f"{combatant.name} suffers {damage} poison damage.")
            if not combatant.is_alive():
                print(f"{combatant.name} has fallen.")


def reduce_status_durations(combatants):
    for combatant in combatants:
        for status, duration in list(combatant.status_effects.items()):
            if duration <= 1:
                del combatant.status_effects[status]
            else:
                combatant.status_effects[status] = duration - 1


def attempt_run(party=None):
    chance = 50
    if party and any(member.has_status("escape_boost") for member in party.members):
        chance = 85

    if random.randint(1, 100) <= chance:
        print("\nThe party escaped!")
        return True

    print("\nCould not escape!")
    return False


def party_turn(party, enemies):
    for member in party.living_members():
        if not enemies:
            break

        while True:
            print(f"\n{member.name}'s turn")
            print("1. Attack")
            print("2. Skill / Spell")
            print("3. Use Item")
            print("4. Defend")
            print("5. Run")
            choice = input("> ").strip()

            if choice == "1":
                if handle_attack(member, enemies, party):
                    break
            elif choice == "2":
                if handle_ability(member, party, enemies):
                    break
            elif choice == "3":
                if use_inventory_item(party, member):
                    break
            elif choice == "4":
                member.defending = True
                print(f"{member.name} braces and will take reduced damage.")
                break
            elif choice == "5":
                if attempt_run(party):
                    return True
                break
            else:
                print("Invalid choice.")

    return False


def enemy_turn(party, enemies):
    for enemy in living_enemies(enemies):
        targets = party.living_members()
        if not targets:
            return

        if enemy.has_status("stagger"):
            print(f"{enemy.name} is staggered and loses its turn.")
            continue

        print(f"\n{enemy.name}'s turn")

        if enemy.behavior == "support":
            wounded_allies = [
                ally for ally in living_enemies(enemies)
                if ally.hp < ally.max_hp
            ]
            if wounded_allies:
                target = min(wounded_allies, key=lambda ally: ally.hp / ally.max_hp)
                healing = max(5, target.max_hp // 4)
                target.heal(healing)
                print(f"{enemy.name} restores {healing} HP to {target.name}.")
                continue

        if enemy.behavior == "resilient" and enemy.hp < enemy.max_hp:
            healing = max(2, enemy.max_hp // 10)
            enemy.heal(healing)
            print(f"{enemy.name} regenerates {healing} HP.")

        target = random.choice(targets)

        if enemy.behavior == "heavy":
            damage = attack(enemy, target, multiplier=1.5, ignore_defense=True)
            if target.is_alive() and damage > 0:
                target.apply_status("exposed", 2)
                print(f"{target.name} is exposed.")
        elif enemy.behavior == "aggressive":
            attack(enemy, target, multiplier=1.25)
        elif enemy.behavior == "drain":
            damage = attack(enemy, target)
            enemy.heal(max(1, damage // 2))
            print(f"{enemy.name} absorbs {max(1, damage // 2)} HP.")
        else:
            attack(enemy, target)
            if (
                enemy.behavior == "poison"
                and target.is_alive()
                and random.random() < 0.5
            ):
                target.apply_status("poison", 3)
                print(f"{target.name} is poisoned.")


def give_rewards(party, defeated_enemies):
    total_exp = sum(enemy.exp_reward for enemy in defeated_enemies)
    total_gold = sum(enemy.gold_reward for enemy in defeated_enemies)

    print("\nVictory!")
    print(f"Gained {total_exp} EXP")
    print(f"Gained {total_gold} Gold")

    for member in party.members:
        gain_exp(member, total_exp)
    if party.members:
        party.members[0].gold += total_gold


def battle(party, area, enemies=None):
    if enemies is None:
        enemies = create_enemy_group(area, party)
    if not enemies:
        print("\nNo enemies appeared.")
        return False

    original_enemies = enemies.copy()
    print(f"\nEnemies appear in the {area}!")
    for enemy in enemies:
        print(f"- {enemy.name}")

    escaped = False

    while party.living_members() and enemies and not escaped:
        participants = party.members + enemies
        apply_round_effects(participants)
        enemies[:] = living_enemies(enemies)

        if not party.living_members():
            break
        if not enemies:
            break

        show_status(party, enemies)
        escaped = party_turn(party, enemies)

        if not escaped and enemies and party.living_members():
            enemy_turn(party, enemies)

        for member in party.members:
            member.defending = False
        reduce_status_durations(participants)

    if escaped:
        for member in party.members:
            member.defending = False
        return False

    if not enemies and party.living_members():
        defeated_enemies = [
            enemy for enemy in original_enemies
            if not enemy.is_alive()
        ]
        give_rewards(party, defeated_enemies)
        for enemy in defeated_enemies:
            party.update_quests("kill", enemy.name)
            for drop in enemy.drops:
                if random.random() < drop.get("chance", 1.0):
                    party.update_quests("collect", drop["item"])
                    from items import create_item
                    item = create_item(drop["item"])
                    if item is not None and party.members:
                        party.members[0].inventory.append(item)
        return True

    print("\nThe party was defeated...")
    for member in party.members:
        member.defending = False
    return False
