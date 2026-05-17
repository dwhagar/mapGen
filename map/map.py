from .room import Room
from .block import Block
from .passage import Passage
from .hallway import Hallway

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
        self.connectivity = {} # To store the graph: {'R1': ['H1'], 'H1': ['R1', 'R2']}

    def add_room(self, room: Room):
        self.rooms.append(room)
        self.connectivity[room.identifier] = []
        for block in room.blocks:
            if block.location:
                self.blocks[block.location] = block

    def add_hallway(self, hallway: Hallway):
        self.hallways.append(hallway)
        self.connectivity[hallway.identifier] = []
        for block in hallway.blocks:
            if block.location:
                self.blocks[block.location] = block

    def add_connection(self, id1, id2):
        """Records a connection between two map areas (rooms or hallways)."""
        if id1 not in self.connectivity: self.connectivity[id1] = []
        if id2 not in self.connectivity: self.connectivity[id2] = []
        
        if id2 not in self.connectivity[id1]: self.connectivity[id1].append(id2)
        if id1 not in self.connectivity[id2]: self.connectivity[id2].append(id1)

    def get_block_at(self, x, y):
        return self.blocks.get((x, y))

    def add_passage(self, passage: Passage):
        self.passages.append(passage)

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
