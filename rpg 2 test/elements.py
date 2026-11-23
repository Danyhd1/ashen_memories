ELEMENTS = (
    "Neutral",
    "Fire",
    "Ice",
    "Lightning",
    "Earth",
    "Water",
    "Wind",
    "Light",
    "Shadow",
    "Poison",
)


ELEMENT_MATRIX = {
    "Neutral": {},
    "Fire": {"Ice": 1.5, "Nature": 1.5, "Fire": 0.5, "Water": 0.5, "Earth": 1.0},
    "Ice": {"Fire": 0.5, "Wind": 1.5, "Earth": 1.5, "Ice": 0.5, "Water": 1.0},
    "Lightning": {"Water": 1.5, "Wind": 1.5, "Earth": 0.5, "Lightning": 0.5},
    "Earth": {"Fire": 1.5, "Lightning": 1.5, "Wind": 0.5, "Ice": 0.5},
    "Water": {"Fire": 1.5, "Earth": 1.5, "Lightning": 0.5, "Water": 0.5, "Ice": 1.0},
    "Wind": {"Earth": 1.5, "Shadow": 1.5, "Lightning": 0.5, "Wind": 0.5},
    "Light": {"Shadow": 1.5, "Undead": 1.5, "Light": 0.5, "Poison": 1.0},
    "Shadow": {"Light": 1.5, "Nature": 1.5, "Shadow": 0.5, "Undead": 0.5},
    "Poison": {"Nature": 1.5, "Water": 1.5, "Poison": 0.5, "Undead": 0.5},
}


def element_multiplier(attack_element, target_element="Neutral", target_type="Beast"):
    if attack_element not in ELEMENT_MATRIX:
        return 1.0

    matrix = ELEMENT_MATRIX[attack_element]
    multiplier = matrix.get(target_element, 1.0)
    type_multiplier = matrix.get(target_type, 1.0)
    return round(multiplier * type_multiplier, 2)
