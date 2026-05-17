from .room import Room
from .block import Block

class Map:
    MIN_ROOMS = 5
    MAX_ROOMS = 30
    
    # Based on A4 paper at 6.35mm per block
    MAX_X = 28  # 0-28 gives 29 blocks wide
    MAX_Y = 42  # 0-42 gives 43 blocks high

    def __init__(self):
        self.rooms = []
        self.blocks = {}  # Using a dictionary with (x, y) tuples as keys for fast lookups

    def add_room(self, room: Room):
        """Adds a room to the map and registers its blocks."""
        self.rooms.append(room)
        for block in room.blocks:
            if block.location:
                # Ensure the block is within the map boundaries
                if 0 <= block.location[0] <= self.MAX_X and 0 <= block.location[1] <= self.MAX_Y:
                    self.blocks[block.location] = block
                else:
                    print(f"Warning: Block at {block.location} is outside the map boundaries and was not added.")

    def get_block_at(self, x, y):
        """Retrieves the block at a given coordinate, or None if it's empty."""
        return self.blocks.get((x, y))
