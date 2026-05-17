from .item import Item

# Object type constants
OBJECT_TYPE_TRAP = 0
OBJECT_TYPE_STATUE = 1
OBJECT_TYPE_FOUNTAIN = 2
OBJECT_TYPE_STAIRS_UP = 3
OBJECT_TYPE_STAIRS_DOWN = 4
OBJECT_TYPE_RUBBLE = 5
OBJECT_TYPE_PILLAR = 6
OBJECT_TYPE_ALTAR = 7
OBJECT_TYPE_THRONE = 8
OBJECT_TYPE_CHEST = 9
OBJECT_TYPE_LEVER = 10
OBJECT_TYPE_BUTTON = 11
OBJECT_TYPE_CHAIR = 12
OBJECT_TYPE_DEAD_BODY = 13
OBJECT_TYPE_TABLE = 14
OBJECT_TYPE_BED = 15
OBJECT_TYPE_POOL = 16


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
