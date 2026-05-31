"""
This module defines the Passage class, which represents a connection between
two adjacent blocks on the map, such as an archway or a door.
"""
import uuid

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
