from .item import Item

class MapObject(Item):
    def __init__(self, object_type, block_uids=None, description=None):
        """
        Initializes a MapObject, which is a feature of the map that cannot be picked up.

        :param object_type: The type of the object, using one of the OBJECT_TYPE constants.
        :param block_uids: A list of unique IDs for the blocks this object occupies.
        :param description: A text description of the object.
        """
        primary_block_uid = block_uids[0] if block_uids else None
        super().__init__(primary_block_uid, description)
        self.object_type = object_type
        self.block_uids = block_uids if block_uids is not None else []

    def get_icon(self):
        return "■"