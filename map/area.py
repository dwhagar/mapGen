"""
This module defines the base Area class, which serves as a parent for specific
area types like Rooms and Hallways.
"""
import uuid

class Area:
    """
    Represents a generic area on the map, composed of a collection of blocks.

    This is the base class for Rooms and Hallways and contains the common logic
    and attributes shared between them.
    """
    def __init__(self, identifier, blocks=None, color=None):
        """
        Initializes an Area instance.

        :param identifier: A unique string identifier for the area (e.g., "R1").
        :param blocks: A list of Block objects that make up the area.
        :param color: The color to use when drawing this area on the PDF map.
        """
        self.identifier = identifier
        self.unique_id = uuid.uuid4()
        self.blocks = blocks if blocks is not None else []
        self.color = color
        self.contents = []  # A list of all content objects within the area.

    def rename(self, new_identifier):
        """
        Updates the identifier of the area.

        :param new_identifier: The new string identifier for the area.
        """
        self.identifier = new_identifier

    def count_passages(self, map_instance):
        """
        Counts how many passages (e.g., doors, archways) are connected to this area.

        :param map_instance: The main map object to access the list of all passages.
        :return: The total number of passages connected to this area.
        """
        passage_count = 0
        for passage in map_instance.passages:
            if passage.side1.area_uid == self.unique_id or passage.side2.area_uid == self.unique_id:
                passage_count += 1
        return passage_count
