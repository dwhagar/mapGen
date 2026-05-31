"""
This module defines the WallDecoration class, which represents a descriptive
feature applied to a wall segment within the map.
"""

class WallDecoration:
    """
    Represents a decoration or feature applied to a continuous segment of a wall.

    A wall decoration adds descriptive text to a specific part of a wall in a room
    or hallway, enhancing the atmosphere and providing more detail for players.
    For example, a decoration could be "a series of faded tapestries" on the
    north wall of a room.
    """
    def __init__(self, locations, direction, description, area_uid):
        """
        Initializes a WallDecoration instance.

        :param locations: A list of (x, y) tuples representing the grid coordinates
                          of the blocks that form the wall segment.
        :param direction: The cardinal direction of the wall relative to the blocks
                          it borders (e.g., 'north', 'south', 'east', 'west').
        :param description: The text description of the decoration (e.g., "a large,
                            ornate mirror").
        :param area_uid: The unique ID of the area (room or hallway) this decoration
                         is associated with.
        """
        self.locations = locations
        self.direction = direction
        self.description = description
        self.area_uid = area_uid
