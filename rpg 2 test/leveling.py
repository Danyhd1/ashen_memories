def exp_needed(level):
    """
    Returns the EXP needed
    for the next level.
    """

    return level * 20


def level_up(character):

    character.level += 1

    character.job.level_up(character)
    from skills import get_skill_points_per_level
    character.skill_points += get_skill_points_per_level(character.magic_type)

    character.hp = character.max_hp
    character.mp = character.max_mp

    print(
        f"\n*** LEVEL UP ***"
    )

    print(
        f"{character.name} "
        f"reached level "
        f"{character.level}!"
    )


def gain_exp(character, amount):

    print(
        f"\nGained {amount} EXP."
    )

    character.exp += amount

    while character.exp >= exp_needed(
        character.level
    ):

        character.exp -= exp_needed(
            character.level
        )

        level_up(character)