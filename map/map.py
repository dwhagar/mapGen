"""
This module defines the Map class, which serves as the main container for all
elements of a generated dungeon map.
"""
from .room import Room
from .block import Block
from .passage import Passage
from .hallway import Hallway
from .wall_decoration import WallDecoration

class Map:
    """
    Represents the entire map structure.

    This class holds all the components of the map, including rooms, hallways,
    the grid of blocks, passages, and wall decorations. It provides methods
    to add and retrieve these components, acting as the central data repository
    for a generated map instance.
    """
    MIN_ROOMS = 5
    MAX_ROOMS = 30

    def __init__(self, width=25, height=25):
        """
        Initializes the Map.

        :param width: The width of the map grid.
        :param height: The height of the map grid.
        """
        self.width = width
        self.height = height
        self.rooms = []
        self.hallways = []
        self.blocks = {}  # Maps (x, y) coordinates to Block objects.
        self.passages = []
        self.wall_decorations = []
        self.connectivity = {}  # Adjacency list for the connectivity graph of areas.
        self.area_by_uid = {}  # Maps area unique IDs to area objects.
        self.block_by_uid = {}  # Maps block unique IDs to block objects.

    def add_room(self, room: Room):
        """
        Adds a room to the map and updates the relevant lookup dictionaries.

        :param room: The Room object to add.
        """
        self.rooms.append(room)
        self.connectivity[room.unique_id] = []
        self.area_by_uid[room.unique_id] = room
        for block in room.blocks:
            if block.location:
                self.blocks[(block.location.x, block.location.y)] = block
                self.block_by_uid[block.unique_id] = block

    def add_hallway(self, hallway: Hallway):
        """
        Adds a hallway to the map and updates the relevant lookup dictionaries.

        :param hallway: The Hallway object to add.
        """
        self.hallways.append(hallway)
        self.connectivity[hallway.unique_id] = []
        self.area_by_uid[hallway.unique_id] = hallway
        for block in hallway.blocks:
            if block.location:
                self.blocks[(block.location.x, block.location.y)] = block
                self.block_by_uid[block.unique_id] = block

    def add_wall_decoration(self, decoration: WallDecoration):
        """
        Adds a wall decoration to the map.

        :param decoration: The WallDecoration object to add.
        """
        self.wall_decorations.append(decoration)

    def add_connection(self, uid1, uid2):
        """
        Records a connection between two map areas in the connectivity graph.

        :param uid1: The unique ID of the first area.
        :param uid2: The unique ID of the second area.
        """
        if uid1 not in self.connectivity: self.connectivity[uid1] = []
        if uid2 not in self.connectivity: self.connectivity[uid2] = []
        
        if uid2 not in self.connectivity[uid1]: self.connectivity[uid1].append(uid2)
        if uid1 not in self.connectivity[uid2]: self.connectivity[uid2].append(uid1)

    def get_block_at(self, x, y):
        """
        Retrieves the block at the given coordinates.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: The Block object at the given coordinates, or None if no block is found.
        """
        return self.blocks.get((x, y))

    def get_block_by_uid(self, uid):
        """
        Retrieves a block by its unique ID.

        :param uid: The unique ID of the block.
        :return: The Block object with the given unique ID, or None if no block is found.
        """
        return self.block_by_uid.get(uid)

    def add_passage(self, passage: Passage):
        """
        Adds a passage to the map's list of passages.

        :param passage: The Passage object to add.
        """
        self.passages.append(passage)

    def get_area_by_identifier(self, identifier):
        """
        Retrieves an area (room or hallway) by its string identifier.

        :param identifier: The identifier of the area (e.g., "R1", "H1").
        :return: The area object, or None if not found.
        """
        for area in self.rooms + self.hallways:
            if area.identifier == identifier:
                return area
        return None

    def get_area_by_uid(self, uid):
        """
        Retrieves an area by its unique ID.

        :param uid: The unique ID of the area.
        :return: The area object, or None if not found.
        """
        return self.area_by_uid.get(uid)

    def get_area_by_location(self, x, y):
        """
        Retrieves the area containing the given coordinates.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: The area object at the location, or None if no area is found.
        """
        block = self.get_block_at(x, y)
        if block:
            return self.get_area_by_uid(block.area_uid)
        return None

    def get_room_by_identifier(self, identifier):
        """
        Retrieves a room by its identifier.

        :param identifier: The identifier of the room.
        :return: The Room object, or None if no room with that identifier is found.
        """
        for room in self.rooms:
            if room.identifier == identifier:
                return room
        return None

    def get_hallway_by_identifier(self, identifier):
        """
        Retrieves a hallway by its identifier.

        :param identifier: The identifier of the hallway.
        :return: The Hallway object, or None if no hallway with that identifier is found.
        """
        for hallway in self.hallways:
            if hallway.identifier == identifier:
                return hallway
        return None
