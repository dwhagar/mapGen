import uuid
from .passage import Passage
from .wall import Wall
from .location import Location

class Block:
    """
    Represents a single square on the map.
    """
    def __init__(self, area_uid=None, location=None, contents=None, floor=None, empty=False):
        """
        Initializes a Block.

        :param area_uid: The unique ID of the area this block belongs to.
        :param location: A Location object representing the block's coordinates.
        :param contents: A list of items, objects, or encounters in the block.
        :param floor: The floor type of the block.
        :param empty: A boolean indicating if the block is empty space.
        """
        self.unique_id = uuid.uuid4()
        self.area_uid = area_uid
        self.location = location
        self.contents = contents if contents is not None else []
        self.floor = floor
        self.north = None
        self.east = None
        self.south = None
        self.west = None
        self.empty = empty

    def get_area(self, map_instance):
        """
        Retrieves the area this block belongs to.

        :param map_instance: The map instance.
        :return: The area object.
        """
        return map_instance.get_area_by_uid(self.area_uid)

    def create_walls(self, map_instance):
        """
        Creates walls for the block based on its neighbors. This function is called
        on all blocks before passages are created. It ensures that walls are
        placed correctly at the boundaries of the map and between different areas.
        """
        if self.empty:
            return

        x, y = self.location.x, self.location.y
        directions = {
            'north': (x, y - 1),
            'east': (x + 1, y),
            'south': (x, y + 1),
            'west': (x - 1, y)
        }
        opposites = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}

        for direction, (nx, ny) in directions.items():
            # Skip if this side of the block already has a wall or passage.
            if getattr(self, direction) is not None:
                continue

            neighbor = map_instance.get_block_at(nx, ny)

            # A wall should be created if the neighbor is non-existent (off-map),
            # is an empty part of the map, or belongs to a different area.
            if not neighbor or neighbor.empty or self.area_uid != neighbor.area_uid:
                wall = Wall()
                setattr(self, direction, wall)
                
                # If the neighbor is a valid block, create the other side of the wall.
                if neighbor and not neighbor.empty:
                    opposite_direction = opposites[direction]
                    # Only set the neighbor's wall if it hasn't been set already.
                    if getattr(neighbor, opposite_direction) is None:
                        setattr(neighbor, opposite_direction, wall)