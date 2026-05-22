from .room import Room
from .block import Block
from .passage import Passage
from .hallway import Hallway
from .wall_decoration import WallDecoration

class Map:
    MIN_ROOMS = 5
    MAX_ROOMS = 30
    
    MAX_X = 28
    MAX_Y = 42

    def __init__(self):
        self.rooms = []
        self.hallways = []
        self.blocks = {}
        self.passages = []
        self.wall_decorations = []
        self.connectivity = {} # To store the graph: {uid: [uid, uid]}
        self.area_by_uid = {}
        self.block_by_uid = {}

    def add_room(self, room: Room):
        self.rooms.append(room)
        self.connectivity[room.unique_id] = []
        self.area_by_uid[room.unique_id] = room
        for block in room.blocks:
            if block.location:
                self.blocks[block.location] = block
                self.block_by_uid[block.unique_id] = block

    def add_hallway(self, hallway: Hallway):
        self.hallways.append(hallway)
        self.connectivity[hallway.unique_id] = []
        self.area_by_uid[hallway.unique_id] = hallway
        for block in hallway.blocks:
            if block.location:
                self.blocks[block.location] = block
                self.block_by_uid[block.unique_id] = block

    def add_wall_decoration(self, decoration: WallDecoration):
        self.wall_decorations.append(decoration)

    def add_connection(self, uid1, uid2):
        """Records a connection between two map areas (rooms or hallways)."""
        if uid1 not in self.connectivity: self.connectivity[uid1] = []
        if uid2 not in self.connectivity: self.connectivity[uid2] = []
        
        if uid2 not in self.connectivity[uid1]: self.connectivity[uid1].append(uid2)
        if uid1 not in self.connectivity[uid2]: self.connectivity[uid2].append(uid1)

    def get_block_at(self, x, y):
        return self.blocks.get((x, y))

    def get_block_by_uid(self, uid):
        return self.block_by_uid.get(uid)

    def add_passage(self, passage: Passage):
        self.passages.append(passage)

    def get_area_by_identifier(self, identifier):
        for area in self.rooms + self.hallways:
            if area.identifier == identifier:
                return area
        return None

    def get_area_by_uid(self, uid):
        return self.area_by_uid.get(uid)

    def get_area_by_location(self, x, y):
        block = self.get_block_at(x, y)
        if block:
            return self.get_area_by_uid(block.area_uid)
        return None

    def get_room_by_identifier(self, identifier):
        for room in self.rooms:
            if room.identifier == identifier:
                return room
        return None

    def get_hallway_by_identifier(self, identifier):
        """Finds a hallway in the map by its unique identifier."""
        for hallway in self.hallways:
            if hallway.identifier == identifier:
                return hallway
        return None