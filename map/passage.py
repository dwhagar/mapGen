"""
This module defines the Passage class, which represents a connection between
two adjacent blocks on the map, such as an archway or a door.
"""
import uuid
import random
from .text import TRAPPED_DOOR_DESCRIPTIONS

class Passage:
    """
    Represents a connection between two adjacent blocks on the map.

    A passage can range from a simple opening to a complex door with various
    attributes like being secret, trapped, or locked. It connects two blocks,
    effectively replacing the wall that would otherwise separate them.
    """
    def __init__(self, side1=None, side2=None, is_door=False, is_secret=False, is_trapped=False, is_locked=False, is_open=False, description=None):
        """
        Initializes a Passage instance.

        :param side1: The Block object on one side of the passage.
        :param side2: The Block object on the other side of the passage.
        :param is_door: A boolean indicating if the passage is a door.
        :param is_secret: A boolean indicating if the door is secret.
        :param is_trapped: A boolean indicating if the door is trapped.
        :param is_locked: A boolean indicating if the door is locked.
        :param is_open: A boolean indicating if the door is currently open.
        :param description: A text description of the passage.
        """
        self.unique_id = uuid.uuid4()
        self.side1 = side1
        self.side2 = side2
        self.is_door = is_door
        self.is_secret = is_secret
        self.is_trapped = is_trapped
        self.is_locked = is_locked
        self.is_open = is_open
        self.description = description
        self.orientation = self._determine_orientation()

    def _determine_orientation(self):
        """
        Determines the orientation of the passage (horizontal or vertical) based on
        the coordinates of the two blocks it connects.

        This is used for drawing the passage symbol correctly on the PDF map.

        :return: 'horizontal' if the blocks are vertically aligned,
                 'vertical' if the blocks are horizontally aligned,
                 or None if the blocks are not set.
        """
        if self.side1 and self.side2:
            # If x-coordinates are the same, the passage is on a horizontal boundary.
            if self.side1.location.x == self.side2.location.x:
                return 'horizontal'
            # If y-coordinates are the same, the passage is on a vertical boundary.
            elif self.side1.location.y == self.side2.location.y:
                return 'vertical'
        return None

    @staticmethod
    def create(the_map, block1, block2, direction, is_door, is_secret=False, is_trapped=False, is_locked=False, is_open=False):
        """
        Creates a Passage object between two adjacent blocks, ensuring consistency with adjacent passages.
        
        This method checks for any passages on the same axis (e.g., a passage in a wall shared by
        multiple rooms). If an adjacent passage is found, its properties (like `is_door`, `is_secret`)
        are copied to the new passage to maintain a uniform appearance. For example, a wide opening
        will consist of multiple passage segments, all of which should be of the same type.

        If no adjacent passage is found, the new passage is created with the specified properties.
        """
        # Determine the orientation of the wall to check for adjacent passages.
        # A passage along a north-south wall should check its east and west neighbors.
        # A passage along an east-west wall should check its north and south neighbors.
        if direction in ['north', 'south']:
            check_directions = [(-1, 0), (1, 0)]  # West, East
        else:  # 'east', 'west'
            check_directions = [(0, -1), (0, 1)]  # North, South

        # Check for an existing adjacent passage to copy its properties.
        for dx, dy in check_directions:
            adj_block = the_map.get_block_at(block1.location.x + dx, block1.location.y + dy)
            if adj_block:
                # Check the same direction on the adjacent block.
                adj_passage = getattr(adj_block, direction, None)
                if isinstance(adj_passage, Passage):
                    # Found an adjacent passage, so copy its properties.
                    is_door = adj_passage.is_door
                    is_secret = adj_passage.is_secret
                    is_trapped = adj_passage.is_trapped
                    is_locked = adj_passage.is_locked
                    is_open = adj_passage.is_open
                    break  # Properties copied, no need to check further.

        # Create the new passage with the determined properties.
        description = random.choice(TRAPPED_DOOR_DESCRIPTIONS) if is_trapped else None
        new_passage = Passage(side1=block1, side2=block2, is_door=is_door, is_secret=is_secret, 
                              is_trapped=is_trapped, is_locked=is_locked, is_open=is_open, 
                              description=description)
        
        # Set the passage on both blocks.
        opposite_direction = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction]
        setattr(block1, direction, new_passage)
        setattr(block2, opposite_direction, new_passage)
        
        # Add the new passage to the map's central list.
        the_map.add_passage(new_passage)
        return True