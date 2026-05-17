class Hallway:
    def __init__(self, identifier, connects_rooms=None, blocks=None, width=1, color=None):
        """
        Initializes a Hallway, which is a collection of blocks connecting two rooms.

        :param identifier: A unique string identifier (e.g., "H1").
        :param connects_rooms: A tuple containing the identifiers of the two rooms it connects.
        :param blocks: A list of Block objects that make up the hallway.
        :param width: The width of the hallway in blocks (e.g., 1 or 2).
        :param color: The color to use when drawing this hallway.
        """
        self.identifier = identifier
        self.connects_rooms = connects_rooms if connects_rooms is not None else (None, None)
        self.blocks = blocks if blocks is not None else []
        self.width = width
        self.color = color
