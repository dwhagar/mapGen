"""
This module defines the MapObject class, representing static objects on the map
such as furniture, statues, or traps.
"""
from .item import Item

class MapObject(Item):
    """
    Represents a static object on the map that is part of the environment.

    MapObjects are features like statues, altars, or rubble that are fixed in
    place and may occupy one or more blocks. They are a type of Item but are
    distinct from collectible items or encounters.
    """
    def __init__(self, object_type, block_uids=None, description=None):
        """
        Initializes a MapObject instance.

        :param object_type: The type of the object, using one of the OBJECT_TYPE constants
                            (e.g., OBJECT_TYPE_STATUE, OBJECT_TYPE_CHEST).
        :param block_uids: A list of unique IDs for the blocks this object occupies.
                           For single-block objects, this will be a list with one ID.
        :param description: A text description of the object.
        """
        # The primary block UID is the first in the list, used for general location reference.
        primary_block_uid = block_uids[0] if block_uids else None
        super().__init__(primary_block_uid, description)
        self.object_type = object_type
        self.block_uids = block_uids if block_uids is not None else []

    def get_icon(self):
        """
        Gets the icon representation for the map object.

        :return: A string character to represent a map object on the map.
        """
        return "■"
