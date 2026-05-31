"""
This module defines the Block class, which is the fundamental unit of the map grid.

Each Block represents a single square on the map and holds information about its
location, contents, and boundaries (walls or passages).
"""
import uuid
from .passage import Passage
from .wall import Wall
from .location import Location

class Block:
    """
    Represents a single square on the map grid.

    A Block is the basic building unit for all areas (rooms and hallways). It keeps
    track of its position, what area it belongs to, what it contains (e.g., items,
    encounters), and what forms its boundaries on all four sides.
    """
    def __init__(self, area_uid=None, location=None, contents=None, floor=None, empty=False):
        """
        Initializes a Block instance.

        :param area_uid: The unique identifier of the Area (Room or Hallway) this block is part of.
        :param location: A Location object specifying the block's x, y coordinates on the map.
        :param contents: A list of map content objects (e.g., Item, Encounter) present in this block.
        :param floor: A description or type of the floor (e.g., 'stone', 'wood'). Currently for future use.
        :param empty: A boolean indicating if this block is part of the playable map area (False)
                      or represents an empty, inaccessible space (True).
        """
        self.unique_id = uuid.uuid4()  # Unique ID for this specific block instance.
        self.area_uid = area_uid      # The ID of the room or hallway this block belongs to.
        self.location = location      # The (x, y) coordinates of the block.
        self.contents = contents if contents is not None else []  # List of objects within the block.
        self.floor = floor            # The type of floor (for descriptive purposes).
        self.north = None             # The boundary on the north side (Wall, Passage, or None).
        self.east = None              # The boundary on the east side.
        self.south = None             # The boundary on the south side.
        self.west = None              # The boundary on the west side.
        self.empty = empty            # True if the block is not part of the generated map structure.

    def get_area(self, map_instance):
        """
        Retrieves the Area (Room or Hallway) object that this block belongs to.

        :param map_instance: The main map object which holds the dictionary of all areas.
        :return: The Area object corresponding to this block's `area_uid`.
        """
        return map_instance.get_area_by_uid(self.area_uid)

    def _set_initial_walls(self, map_instance):
        """
        Sets the initial walls for the block based on its neighboring blocks.

        This method is called when a block is first created and assigned to an area.
        It checks each of its four neighbors to determine if a wall should be placed
        on that side. A wall is created if the adjacent space is outside the map,
        is an 'empty' block, or belongs to a different area.

        :param map_instance: The main map object, used to access neighbor information.
        """
        if self.empty:
            return

        x, y = self.location.x, self.location.y
        # Define the relative coordinates for each direction
        directions = {
            'north': (x, y - 1),
            'east': (x + 1, y),
            'south': (x, y + 1),
            'west': (x - 1, y)
        }
        # Map directions to their opposites for setting walls on neighbors
        opposites = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}

        for direction, (nx, ny) in directions.items():
            # If a boundary (like a passage) is already set, skip it.
            if getattr(self, direction) is not None:
                continue

            neighbor = map_instance.get_block_at(nx, ny)

            # A wall is needed if there's no neighbor, the neighbor is empty space,
            # or the neighbor belongs to a different room/hallway.
            wall_needed = not neighbor or neighbor.empty or self.area_uid != neighbor.area_uid
            
            if wall_needed:
                wall = Wall()
                setattr(self, direction, wall)
                
                # If there is a neighbor, set the corresponding wall on it to ensure consistency.
                if neighbor:
                    opposite_direction = opposites[direction]
                    # Only set the neighbor's wall if it's not already defined (e.g., as a Passage).
                    if getattr(neighbor, opposite_direction) is None:
                        setattr(neighbor, opposite_direction, wall)
            else:
                # If no wall is needed (i.e., it's an open connection to a block in the same area),
                # ensure no Wall object is present. This is a cleanup for potential edge cases.
                if isinstance(getattr(self, direction), Wall):
                    setattr(self, direction, None)
