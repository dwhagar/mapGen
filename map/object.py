from .item import Item

class MapObject(Item):
    def __init__(self, object_type, room_identifier=None, block_locations=None, description=None):
        """
        Initializes a MapObject, which is a feature of the map that cannot be picked up.

        :param object_type: The type of the object, using one of the OBJECT_TYPE constants.
        :param room_identifier: The identifier of the room this object is in.
        :param block_locations: A list of (x, y) tuples representing the blocks this object occupies.
        :param description: A text description of the object.
        """
        # The base Item class still uses a single location. For multi-block objects,
        # we can use the first location in the list as the primary reference point.
        primary_location = block_locations[0] if block_locations else None
        super().__init__(room_identifier, primary_location, description)
        self.object_type = object_type
        self.block_locations = block_locations if block_locations is not None else []
