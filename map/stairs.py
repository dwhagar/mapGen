"""
This module defines the Stairs class, a specific type of MapObject that
represents a staircase leading up or down.
"""
import random
from .object import MapObject
from .text import OBJECT_NOUNS
from .constants import OBJECT_TYPE_STAIRS_UP, OBJECT_TYPE_STAIRS_DOWN

class Stairs(MapObject):
    """
    Represents a staircase on the map, which can lead either up or down.

    Stairs are a specialized form of MapObject with a specific direction. They
    have a distinct icon and description based on whether they ascend or descend.
    """
    def __init__(self, block_uid, direction=None, position=""):
        """
        Initializes a Stairs instance.

        If no direction is specified, it will be chosen randomly.

        :param block_uid: The unique ID of the block where the stairs are located.
        :param direction: The direction of the stairs, either 'up' or 'down'.
        :param position: A descriptive string for the stairs' location within the area,
                         e.g., "in the corner".
        """
        if direction is None:
            direction = random.choice(["up", "down"])
        if direction not in ["up", "down"]:
            raise ValueError("Direction must be 'up' or 'down'")
        self.direction = direction
        
        # Determine the object type and generate a description based on the direction.
        object_type = OBJECT_TYPE_STAIRS_UP if self.direction == "up" else OBJECT_TYPE_STAIRS_DOWN
        description = f"There is a {OBJECT_NOUNS[object_type]} {position}."
        super().__init__(object_type, [block_uid], description)

    def get_icon(self):
        """
        Gets the icon representation for the stairs.

        :return: A string character ('▲' for up, '▼' for down) to represent
                 the stairs on the map.
        """
        return "▲" if self.direction == "up" else "▼"

    def set_direction(self, direction):
        """
        Sets the direction of the stairs and updates the description accordingly.

        :param direction: The new direction for the stairs, either 'up' or 'down'.
        """
        if direction not in ["up", "down"]:
            raise ValueError("Direction must be 'up' or 'down'")
        self.direction = direction
        
        # Re-generate the description to reflect the new direction.
        # This is a simple way to preserve the position part of the description.
        position = self.description.split(" ")[-1] 
        object_type = OBJECT_TYPE_STAIRS_UP if self.direction == "up" else OBJECT_TYPE_STAIRS_DOWN
        self.description = f"There is a {OBJECT_NOUNS[object_type]} {position}."
