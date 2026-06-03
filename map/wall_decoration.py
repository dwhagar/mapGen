"""
This module defines the WallDecoration class and handles the logic for decorating wall segments.
"""
import random
from collections import defaultdict
from .constants import WALL_DECORATION_CHANCE
from .text import WALL_DECORATIONS
from .wall import Wall

def decorate_walls(the_map):
    """
    Adds descriptive decorations to random wall segments throughout the map.
    This function identifies continuous wall segments within each area and randomly
    applies a decoration to some of them, adding flavor and detail to the map.
    """
    print("Decorating walls...")
    
    # Step 1: Group all wall locations by the area they belong to and their direction.
    walls_by_area = defaultdict(lambda: defaultdict(list))
    for block in the_map.blocks.values():
        if block.empty or not block.area_uid:
            continue
        for direction in ['north', 'south', 'east', 'west']:
            if isinstance(getattr(block, direction), Wall):
                walls_by_area[block.area_uid][direction].append(block.location)

    # Step 2: For each area, find continuous wall segments and randomly decorate them.
    for area_uid, walls_by_direction in walls_by_area.items():
        for direction, locations in walls_by_direction.items():
            # The primary axis for sorting depends on the wall's orientation.
            # For north/south walls, sort by x-coordinate. For east/west, sort by y.
            sort_axis = 0 if direction in ['north', 'south'] else 1
            
            continuous_segments = _group_continuous_locations(locations, sort_axis)
            
            for segment in continuous_segments:
                # Give each segment a chance to be decorated.
                if random.random() < WALL_DECORATION_CHANCE:
                    description = random.choice(WALL_DECORATIONS)
                    decoration = WallDecoration(locations=segment, direction=direction, 
                                                description=description, area_uid=area_uid)
                    the_map.add_wall_decoration(decoration)

def _group_continuous_locations(locations, sort_axis):
    """
    Groups a list of Location objects into continuous segments based on their
    coordinates. This is used to identify unbroken stretches of walls.

    :param locations: A list of Location objects to be grouped.
    :param sort_axis: The axis to sort by (0 for x, 1 for y). This determines
                      how continuity is checked.
    :return: A list of lists, where each inner list is a continuous segment of locations.
    """
    if not locations:
        return []

    # Sort locations to make finding continuous segments straightforward.
    # For north/south walls, sort by x-coordinate. For east/west walls, sort by y.
    sorted_locations = sorted(locations, key=lambda loc: (loc.x, loc.y) if sort_axis == 0 else (loc.y, loc.x))
    
    segments = []
    if not sorted_locations:
        return segments
        
    current_segment = [sorted_locations[0]]
    
    for i in range(1, len(sorted_locations)):
        prev_loc = current_segment[-1]
        curr_loc = sorted_locations[i]
        
        # Check if the current location is adjacent to the previous one on the primary axis.
        is_continuous = (sort_axis == 0 and curr_loc.x == prev_loc.x + 1 and curr_loc.y == prev_loc.y) or \
                        (sort_axis == 1 and curr_loc.y == prev_loc.y + 1 and curr_loc.x == prev_loc.x)
        
        if is_continuous:
            current_segment.append(curr_loc)
        else:
            segments.append(current_segment)
            current_segment = [curr_loc]
            
    # Add the last segment.
    segments.append(current_segment)
    return segments

class WallDecoration:
    """
    Represents a decoration or feature applied to a continuous segment of a wall.
    This class stores the information needed to describe the decoration, including its
    location, orientation, and a text description.
    """
    def __init__(self, locations, direction, description, area_uid):
        """
        Initializes a WallDecoration instance.

        :param locations: A list of Location objects that make up the wall segment.
        :param direction: The cardinal direction of the wall (e.g., 'north', 'south').
        :param description: The text description of the decoration (e.g., "covered in moss").
        :param area_uid: The unique ID of the area (room or hallway) this decoration is in.
        """
        self.locations = locations
        self.direction = direction
        self.description = description
        self.area_uid = area_uid