from .passage import Passage
from .wall import Wall


class Block:
    def __init__(self, north=None, east=None, south=None, west=None, contents=None, floor=None, room_identifier=None, location=None):
        """
        Initializes a Block, a fundamental component of the map.

        Each directional attribute (north, east, south, west) defines the boundary of the block and what it connects to.
        It can be one of the following:
        - A 'Passage' object: This indicates a connection to another Block. The Passage object itself holds references
          to the two blocks it connects.
        - A 'Wall' object: This represents a solid boundary, terminating the connection in that direction.
        - 'None': This represents an open floor with no defined boundary, wall, or passage.

        :param north: The object on the north side (Passage, Wall, or None).
        :param east: The object on the east side (Passage, Wall, or None).
        :param south: The object on the south side (Passage, Wall, or None).
        :param west: The object on the west side (Passage, Wall, or None).
        :param contents: A list of items or obstacles within the block.
        :param floor: A string or object describing the floor type (e.g., 'water', 'trap').
        :param room_identifier: The identifier of the room this block belongs to.
        :param location: An (x, y) tuple representing the block's coordinates.
        """
        self.north = north
        self.east = east
        self.south = south
        self.west = west
        self.contents = contents if contents is not None else []
        self.floor = floor
        self.room_identifier = room_identifier
        self.location = location
