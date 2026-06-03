"""
This module provides utility functions used across the map generation package.

It includes functions for weighted random selections, calculating geometric
properties of map areas, and comparing map elements.
"""
import random
import heapq
from .constants import *
from .passage import Passage


def _get_weighted_random_type(choices):
    """
    Selects a random key from a dictionary of weighted choices.

    This helper function takes a dictionary where keys are the items to be chosen
    and values are their corresponding probabilities (weights). It handles cases
    where the total probability is not 1, making it flexible for various use cases.

    :param choices: A dictionary where keys are the types and values are their probabilities.
    :return: A randomly selected key based on the provided weights. Returns None if the
             choices dictionary is empty or all weights are zero.
    """
    total_probability = sum(choices.values())
    if total_probability == 0:
        return None

    # Generate a random number in the range of the total probability.
    roll = random.uniform(0, total_probability)
    
    # Iterate through the choices and find which "bucket" the roll falls into.
    cumulative_probability = 0
    for item_type, probability in choices.items():
        cumulative_probability += probability
        if roll < cumulative_probability:
            return item_type
    
    # This part should ideally not be reached if logic is correct, but as a fallback,
    # it returns the last item, which can help in debugging.
    return list(choices.keys())[-1]

def get_random_object_type():
    """
    Returns a random object type based on the probabilities defined in `constants.py`.
    This function aggregates all object probabilities into a single dictionary and
    uses a weighted random selection to determine the chosen object type.
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
        OBJECT_TYPE_BED: OBJECT_PROB_BED,
        OBJECT_TYPE_POOL: OBJECT_PROB_POOL,
    }
    return _get_weighted_random_type(object_probabilities)

def get_random_item_type():
    """
    Returns a random item type based on the probabilities defined in `constants.py`.
    This function aggregates all item probabilities into a single dictionary and
    uses a weighted random selection to determine the chosen item type.
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
    Returns a random encounter type based on the probabilities defined in `constants.py`.
    This function aggregates all encounter probabilities into a single dictionary and
    uses a weighted random selection to determine the chosen encounter type.
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
    Calculates the geometric center of a list of blocks. This is useful for determining
    the central point of a room or hallway, which can be used for labeling, pathfinding,
    or other geometric operations.

    :param blocks: A list of Block objects.
    :return: A tuple (x, y) representing the center coordinates. Returns (0, 0) if the
             list is empty, which should be handled by the caller.
    """
    if not blocks:
        return (0, 0)  # Return a default value for empty lists.
    
    x_coords = [b.location.x for b in blocks]
    y_coords = [b.location.y for b in blocks]
    
    # Using integer division to ensure the center is on the grid.
    center_x = sum(x_coords) // len(x_coords)
    center_y = sum(y_coords) // len(y_coords)
    
    return (center_x, center_y)

def get_relative_direction_from_center(segment_locations, center):
    """
    Determines the cardinal direction of a wall segment relative to the center of its area.
    This is used for generating descriptive text, such as "On the northern wall...".
    The function calculates the average position of the wall segment and compares it
    to the area's center to determine the most appropriate cardinal direction.

    :param segment_locations: A list of Location objects for the wall segment.
    :param center: A tuple (x, y) for the center of the area.
    :return: A string representing the cardinal direction (e.g., "northern", "eastern", "central").
    """
    if not segment_locations:
        return "central"  # Default to central if there are no locations.

    segment_center_x = sum(loc.x for loc in segment_locations) / len(segment_locations)
    segment_center_y = sum(loc.y for loc in segment_locations) / len(segment_locations)
    
    dx = segment_center_x - center[0]
    dy = segment_center_y - center[1]

    # If the segment is very close to the center, it's considered central.
    if abs(dx) < 1.5 and abs(dy) < 1.5:
        return "central"

    # Determine the dominant direction.
    if abs(dy) > abs(dx):
        return "northern" if dy > 0 else "southern"
    else:
        return "eastern" if dx > 0 else "western"

def compare_passages(p1, p2):
    """
    Compares two Passage objects to determine if they are functionally identical.
    This function checks for equality in key attributes like door status and orientation,
    and also verifies that they connect the same blocks, regardless of the order of
    `side1` and `side2`.

    :param p1: The first Passage object.
    :param p2: The second Passage object.
    :return: True if the passages are functionally the same, False otherwise.
    """
    if not p1 and not p2:
        return True
    if not p1 or not p2:
        return False

    # Check basic properties first for a quick exit.
    if p1.is_door != p2.is_door or p1.orientation != p2.orientation:
        return False

    # If orientation is not defined, we can't reliably compare them.
    if p1.orientation is None:
        return True

    # For a robust comparison, check that the connected blocks are the same.
    # We use sets to ignore the order of side1 and side2.
    p1_sides = {p1.side1.location, p1.side2.location}
    p2_sides = {p2.side1.location, p2.side2.location}

    return p1_sides == p2_sides

def heuristic(a, b):
    """
    Calculates the Manhattan distance between two points (a, b). This heuristic is
    used by the A* pathfinding algorithm to estimate the distance to the target.
    It's a common choice for grid-based pathfinding because it's fast and admissible.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def find_path_astar(the_map, start, end):
    """
    Finds a path between two points using the A* algorithm. The pathfinding prefers
    empty space and heavily penalizes paths that go through existing rooms to ensure
    hallways are created in unoccupied areas.

    :param the_map: The Map object to pathfind on.
    :param start: The starting (x, y) coordinate.
    :param end: The ending (x, y) coordinate.
    :return: A list of (x, y) tuples representing the path, or None if no path is found.
    """
    open_set = [(0, start)]  # Priority queue: (f_score, location)
    came_from = {}
    g_score = { (x, y): float('inf') for x in range(the_map.width + 2) for y in range(the_map.height + 2) }
    g_score[start] = 0
    f_score = { (x, y): float('inf') for x in range(the_map.width + 2) for y in range(the_map.height + 2) }
    f_score[start] = heuristic(start, end)

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == end:
            # Reconstruct the path from end to start.
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)  # Add the start node.
            return path[::-1]

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor_loc = (current[0] + dx, current[1] + dy)
            if not (1 <= neighbor_loc[0] <= the_map.width and 1 <= neighbor_loc[1] <= the_map.height):
                continue

            # Cost is higher for moving through an existing room.
            block = the_map.get_block_at(neighbor_loc[0], neighbor_loc[1])
            cost = HALLWAY_OBSTACLE_COST if block and not block.empty and neighbor_loc != end else 1

            tentative_g_score = g_score[current] + cost
            if tentative_g_score < g_score.get(neighbor_loc, float('inf')):
                came_from[neighbor_loc] = current
                g_score[neighbor_loc] = tentative_g_score
                f_score[neighbor_loc] = tentative_g_score + heuristic(neighbor_loc, end)
                heapq.heappush(open_set, (f_score[neighbor_loc], neighbor_loc))
                
    return None  # No path found.

def is_area_free(the_map, x, y, width, height):
    """
    Checks if a rectangular area on the map is free to be occupied. This is crucial
    for placing new rooms without overlapping existing ones. The function also includes
    a small buffer around the area to ensure rooms are not placed directly adjacent
    to each other, which can improve map readability.

    :param the_map: The Map object.
    :param x: The starting x-coordinate of the area.
    :param y: The starting y-coordinate of the area.
    :param width: The width of the area.
    :param height: The height of the area.
    :return: True if the area is free, False otherwise.
    """
    # Check a slightly larger area to create a buffer around the room.
    for i in range(y - 1, y + height + 1):
        for j in range(x - 1, x + width + 1):
            # Ensure the coordinates are within the map boundaries.
            if not (1 <= j <= the_map.width and 1 <= i <= the_map.height):
                return False
            
            block = the_map.get_block_at(j, i)
            if block and not block.empty:
                return False
    return True


def is_safe_to_punch_passage(the_map, block, direction):
    """
    Checks if it's safe to create a passage in a certain direction from a block.
    This function prevents creating passages that are directly adjacent to each other
    on the same axis, which can lead to unintended wide openings.

    :param the_map: The Map object.
    :param block: The Block to create the passage from.
    :param direction: The direction of the passage ('north', 'south', 'east', 'west').
    :return: True if it's safe to create the passage, False otherwise.
    """
    x, y = block.location.x, block.location.y
    
    # Determine which neighbors to check based on the passage direction.
    if direction in ['north', 'south']:
        # For a vertical passage, check the blocks to the east and west.
        check_coords = [(x - 1, y), (x + 1, y)]
    elif direction in ['east', 'west']:
        # For a horizontal passage, check the blocks to the north and south.
        check_coords = [(x, y - 1), (x, y + 1)]
    else:
        return True  # Should not happen with valid directions.

    for cx, cy in check_coords:
        adj_block = the_map.get_block_at(cx, cy)
        if adj_block:
            # Check if the adjacent block also has a passage in the same direction.
            if isinstance(getattr(adj_block, direction, None), Passage):
                return False

    return True