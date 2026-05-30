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

    def _set_initial_walls(self, map_instance):
        """
        Sets initial walls for the block based on its neighbors. This is called
        when the block is first assigned to an area (room or hallway).
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

        print(f"DEBUG: Processing walls for block {self.location} (Area: {self.area_uid})") # Debug print

        for direction, (nx, ny) in directions.items():
            # Skip if this side of the block already has a wall or passage.
            if getattr(self, direction) is not None:
                print(f"DEBUG:   Block {self.location} {direction} already has {getattr(self, direction).__class__.__name__}. Skipping.") # Debug print
                continue

            neighbor = map_instance.get_block_at(nx, ny)
            neighbor_info = f"Neighbor {direction} at ({nx},{ny}): "
            if neighbor:
                neighbor_info += f"Area: {neighbor.area_uid}, Empty: {neighbor.empty}"
            else:
                neighbor_info += "None (off-map)"
            print(f"DEBUG:   {neighbor_info}") # Debug print

            # Determine if a wall is needed
            wall_needed = False
            if not neighbor:
                wall_needed = True
                print(f"DEBUG:     Wall needed for {self.location} {direction}: No neighbor (off-map boundary)") # Debug print
            elif neighbor.empty:
                wall_needed = True
                print(f"DEBUG:     Wall needed for {self.location} {direction}: Neighbor is empty space") # Debug print
            elif self.area_uid != neighbor.area_uid:
                wall_needed = True
                print(f"DEBUG:     Wall needed for {self.location} {direction}: Neighbor is in different area") # Debug print
            else:
                print(f"DEBUG:     No wall needed for {self.location} {direction}: Same area, not empty") # Debug print
            
            if wall_needed:
                wall = Wall()
                setattr(self, direction, wall)
                print(f"DEBUG:     Wall object {wall} set for {self.location} {direction}") # Debug print
                
                # If the neighbor is a valid block, ensure it also has this wall set.
                # This ensures consistency and that the wall is represented from both sides.
                # Only set the neighbor's wall if it hasn't been set already (e.g., by a passage).
                if neighbor:
                    opposite_direction = opposites[direction]
                    if getattr(neighbor, opposite_direction) is None:
                        setattr(neighbor, opposite_direction, wall)
                        print(f"DEBUG:     Wall object {wall} also set for neighbor {neighbor.location} {opposite_direction}") # Debug print
                    else:
                        print(f"DEBUG:     Neighbor {neighbor.location} {opposite_direction} already has {getattr(neighbor, opposite_direction).__class__.__name__}. Not overwriting.") # Debug print
            else:
                # If no wall is needed, ensure no Wall object is present (could be from a previous run or bug)
                if isinstance(getattr(self, direction), Wall):
                    print(f"DEBUG:     WARNING: Block {self.location} {direction} has a Wall but no wall was determined needed. Clearing.")
                    setattr(self, direction, None)
