import random
from .constants import *

def _get_weighted_random_type(choices):
    """
    Returns a random type based on a dictionary of weighted choices.
    :param choices: A dictionary where keys are types and values are their probabilities.
    """
    total_probability = sum(choices.values())
    if total_probability == 0:
        return None # Or raise an error, depending on desired behavior

    roll = random.uniform(0, total_probability)
    cumulative_probability = 0
    for item_type, probability in choices.items():
        cumulative_probability += probability
        if roll < cumulative_probability:
            return item_type
    
    # Fallback in case of floating point inaccuracies, return the last item
    return list(choices.keys())[-1]

def get_random_object_type():
    """
    Returns a random object type based on the probabilities in constants.py.
    """
    object_probabilities = {
        OBJECT_TYPE_TRAP: OBJECT_PROB_TRAP,
        OBJECT_TYPE_STATUE: OBJECT_PROB_STATUE,
        OBJECT_TYPE_FOUNTAIN: OBJECT_PROB_FOUNTAIN,
        OBJECT_TYPE_STAIRS_UP: OBJECT_PROB_STAIRS_UP,
        OBJECT_TYPE_STAIRS_DOWN: OBJECT_PROB_STAIRS_DOWN,
        OBJECT_TYPE_RUBBLE: OBJECT_PROB_RUBBLE,
        OBJECT_TYPE_PILLAR: OBJECT_PROB_PILLAR,
        OBJECT_TYPE_ALTAR: OBJECT_PROB_ALTAR,
        OBJECT_TYPE_THRONE: OBJECT_PROB_THRONE,
        OBJECT_TYPE_CHEST: OBJECT_PROB_CHEST,
        OBJECT_TYPE_LEVER: OBJECT_PROB_LEVER,
        OBJECT_TYPE_BUTTON: OBJECT_PROB_BUTTON,
        OBJECT_TYPE_CHAIR: OBJECT_PROB_CHAIR,
        OBJECT_TYPE_DEAD_BODY: OBJECT_PROB_DEAD_BODY,
        OBJECT_TYPE_TABLE: OBJECT_PROB_TABLE,
        OBJECT_TYPE_POOL: OBJECT_PROB_POOL,
    }
    return _get_weighted_random_type(object_probabilities)

def get_random_item_type():
    """
    Returns a random item type based on the probabilities in constants.py.
    """
    item_probabilities = {
        ITEM_TYPE_POTION: ITEM_PROB_POTION,
        ITEM_TYPE_SCROLL: ITEM_PROB_SCROLL,
        ITEM_TYPE_WEAPON: ITEM_PROB_WEAPON,
        ITEM_TYPE_ARMOR: ITEM_PROB_ARMOR,
        ITEM_TYPE_GOLD: ITEM_PROB_GOLD,
    }
    return _get_weighted_random_type(item_probabilities)

def get_random_encounter_type():
    """
    Returns a random encounter type based on the probabilities in constants.py.
    """
    encounter_probabilities = {
        ENCOUNTER_TYPE_MONSTER: ENCOUNTER_PROB_MONSTER,
        ENCOUNTER_TYPE_ANIMAL: ENCOUNTER_PROB_ANIMAL,
        ENCOUNTER_TYPE_UNDEAD: ENCOUNTER_PROB_UNDEAD,
        ENCOUNTER_TYPE_SWARM: ENCOUNTER_PROB_SWARM,
    }
    return _get_weighted_random_type(encounter_probabilities)

def get_center_of_blocks(blocks):
    """
    Calculates the center of a list of blocks.

    :param blocks: A list of Block objects.
    :return: A tuple representing the center coordinates, or None if the list is empty.
    """
    if not blocks: return None
    x_coords = [b.location.x for b in blocks]
    y_coords = [b.location.y for b in blocks]
    return (sum(x_coords) // len(x_coords), sum(y_coords) // len(y_coords))

def get_relative_direction_from_center(segment_locations, center):
    """
    Determines the direction of a segment relative to a center point.
    """
    segment_center_x = sum(loc.x for loc in segment_locations) / len(segment_locations)
    segment_center_y = sum(loc.y for loc in segment_locations) / len(segment_locations)
    
    dx = segment_center_x - center[0]
    dy = segment_center_y - center[1]

    if abs(dx) < 2 and abs(dy) < 2:
        return "central"

    if dy > abs(dx):
        return "northern"
    elif dy < -abs(dx):
        return "southern"
    elif dx > abs(dy):
        return "eastern"
    else:
        return "western"

def compare_passages(passage1, passage2):
    """
    Compares two Passage objects to see if they are functionally identical.
    Excludes unique_id from the comparison.

    :param passage1: The first Passage object.
    :param passage2: The second Passage object.
    :return: True if the passages are identical, False otherwise.
    """
    if not passage1 and not passage2:
        return True
    if not passage1 or not passage2:
        return False

    if passage1.is_door != passage2.is_door:
        return False

    if passage1.orientation != passage2.orientation:
        return False

    if passage1.orientation is None:
        return True

    # Compare sides. The order of side1 and side2 might be swapped.
    p1_sides = {(passage1.side1.location, passage1.side1.area_uid), (passage1.side2.location, passage1.side2.area_uid)}
    p2_sides = {(passage2.side1.location, passage2.side1.area_uid), (passage2.side2.location, passage2.side2.area_uid)}

    return p1_sides == p2_sides