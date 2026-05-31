"""
This module defines the base class for all content that can be placed on the map.

The Item class serves as a parent class for more specific content types like
Encounters, MapObjects, etc. It provides a common interface for objects that
can be located within a block on the map.
"""
import uuid

class Item:
    """
    Represents a generic item or content that can be placed in a Block.

    This is the base class for any object that can be part of a block's contents,
    such as treasures, encounters, or static map objects. It holds a unique
    identifier and a reference to the block it is in.
    """
    def __init__(self, block_uid=None, description=None):
        """
        Initializes a new Item instance.

        :param block_uid: The unique ID of the block where this item is located.
        :param description: A text description of the item.
        """
        self.unique_id = uuid.uuid4()  # A unique identifier for this specific item instance.
        self.block_uid = block_uid      # The ID of the block this item belongs to.
        self.description = description  # A textual description of the item.

    def get_block(self, map_instance):
        """
        Retrieves the Block object where this item is located.

        :param map_instance: The main map object which can resolve UIDs to objects.
        :return: The Block object corresponding to this item's `block_uid`.
        """
        return map_instance.get_block_by_uid(self.block_uid)
