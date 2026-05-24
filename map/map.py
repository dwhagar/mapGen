from .room import Room
from .block import Block
from .passage import Passage
from .hallway import Hallway
from .wall_decoration import WallDecoration

class Map:
    """
    Represents the entire map, including all its rooms, hallways, and blocks.
    """
    MIN_ROOMS = 5
    MAX_ROOMS = 30

    def __init__(self, width=25, height=25):
        """
        Initializes the Map.
        """
        self.width = width
        self.height = height
        self.rooms = []
        self.hallways = []
        self.blocks = {}
        self.passages = []
        self.wall_decorations = []
        self.connectivity = {} # To store the graph: {uid: [uid, uid]}
        self.area_by_uid = {}
        self.block_by_uid = {}

    def add_room(self, room: Room):
        """
        Adds a room to the map.

        :param room: The room to add.
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
        Adds a hallway to the map.

        :param hallway: The hallway to add.
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

        :param decoration: The wall decoration to add.
        """
        self.wall_decorations.append(decoration)

    def add_connection(self, uid1, uid2):
        """
        Records a connection between two map areas (rooms or hallways).

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
        :return: The block at the given coordinates, or None if no block is found.
        """
        return self.blocks.get((x, y))

    def get_block_by_uid(self, uid):
        """
        Retrieves a block by its unique ID.

        :param uid: The unique ID of the block.
        :return: The block with the given unique ID, or None if no block is found.
        """
        return self.block_by_uid.get(uid)

    def add_passage(self, passage: Passage):
        """
        Adds a passage to the map.

        :param passage: The passage to add.
        """
        self.passages.append(passage)

    def get_area_by_identifier(self, identifier):
        """
        Retrieves an area by its identifier.

        :param identifier: The identifier of the area.
        :return: The area with the given identifier, or None if no area is found.
        """
        for area in self.rooms + self.hallways:
            if area.identifier == identifier:
                return area
        return None

    def get_area_by_uid(self, uid):
        """
        Retrieves an area by its unique ID.

        :param uid: The unique ID of the area.
        :return: The area with the given unique ID, or None if no area is found.
        """
        return self.area_by_uid.get(uid)

    def get_area_by_location(self, x, y):
        """
        Retrieves the area at the given coordinates.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        :return: The area at the given coordinates, or None if no area is found.
        """
        block = self.get_block_at(x, y)
        if block:
            return self.get_area_by_uid(block.area_uid)
        return None

    def get_room_by_identifier(self, identifier):
        """
        Retrieves a room by its identifier.

        :param identifier: The identifier of the room.
        :return: The room with the given identifier, or None if no room is found.
        """
        for room in self.rooms:
            if room.identifier == identifier:
                return room
        return None

    def get_hallway_by_identifier(self, identifier):
        """
        Finds a hallway in the map by its unique identifier.

        :param identifier: The identifier of the hallway.
        :return: The hallway with the given identifier, or None if no hallway is found.
        """
        for hallway in self.hallways:
            if hallway.identifier == identifier:
                return hallway
        return None