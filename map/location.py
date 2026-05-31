"""
This module defines location-based classes, including Location and Area.
It seems there might be some redundancy with the Room and Hallway classes.
The Area class here appears to be a more generic version of what Room and Hallway
classes accomplish.
"""
from .passage import Passage

class Location:
    """
    Represents a simple coordinate pair (x, y) on the map grid.
    """
    def __init__(self, x, y):
        """
        Initializes a Location instance.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        """
        self.x = x
        self.y = y

class Area(Location):
    """
    Represents a generic area on the map, such as a room or a hallway.

    NOTE: This class seems to have overlapping responsibilities with the `Room` and
    `Hallway` classes. It might be a candidate for refactoring or removal to
    consolidate the concept of a map area into a more unified structure.
    """
    def __init__(self, identifier, blocks=None, color=None):
        """
        Initializes an Area instance.

        :param identifier: A string identifier for the area (e.g., "R1").
        :param blocks: A list of Block objects that constitute this area.
        :param color: A color for drawing the area on the map.
        """
        super().__init__(x=0, y=0) # The x, y from Location seem unused here.
        self.identifier = identifier
        self.blocks = blocks if blocks is not None else []
        self.unique_id = f"{self.identifier}-{id(self)}"
        self.color = color

    def __str__(self):
        """
        Returns the string representation of the area, which is its identifier.
        """
        return self.identifier

    def count_passages(self, map_instance):
        """
        Counts the number of unique passages connected to this area.

        This method iterates through the blocks of the area and checks their
        boundaries for Passage objects that lead to a different area.

        :param map_instance: The main map object.
        :return: The number of unique passages connected to this area.
        """
        passage_uids = set()
        for block in self.blocks:
            for direction in ['north', 'south', 'east', 'west']:
                connection = getattr(block, direction)
                if isinstance(connection, Passage):
                    # Check if the passage connects to a different area to count it as an exit.
                    if connection.side1.area_uid != self.unique_id or connection.side2.area_uid != self.unique_id:
                        passage_uids.add(connection.unique_id)
        return len(passage_uids)

    def rename(self, new_identifier):
        """
        Renames the area and updates its unique ID.

        :param new_identifier: The new string identifier for the area.
        """
        self.identifier = new_identifier
        self.unique_id = f"{self.identifier}-{id(self)}"
