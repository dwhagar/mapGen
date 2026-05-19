class WallDecoration:
    """
    Represents a decoration applied to a segment of a wall.
    A wall segment is a continuous, straight line of walls.
    """
    def __init__(self, locations, direction, description):
        """
        Initializes a WallDecoration.

        :param locations: A list of (x, y) tuples for the blocks forming the wall segment.
        :param direction: The direction of the wall relative to the blocks (e.g., 'north').
        :param description: The text description of the decoration.
        """
        self.locations = locations
        self.direction = direction
        self.description = description

    def get_room_identifier(self, map_instance):
        """
        Determines which room this wall decoration is primarily in.
        """
        if not self.locations:
            return None
        
        # Just use the first block to identify the room
        first_block_loc = self.locations[0]
        block = map_instance.get_block_at(first_block_loc[0], first_block_loc[1])
        if block:
            return block.room_identifier
        return None