class Hallway:
    def __init__(self, connects_rooms=None, blocks=None, width=1):
        """
        Initializes a Hallway, which is a collection of blocks connecting two rooms.

        :param connects_rooms: A tuple containing the identifiers of the two rooms it connects.
        :param blocks: A list of Block objects that make up the hallway.
        :param width: The width of the hallway in blocks (e.g., 1 or 2).
        """
        self.connects_rooms = connects_rooms if connects_rooms is not None else (None, None)
        self.blocks = blocks if blocks is not None else []
        self.width = width
