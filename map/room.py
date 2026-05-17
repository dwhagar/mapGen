class Room:
    def __init__(self, identifier, blocks=None):
        self.identifier = identifier
        self.blocks = blocks if blocks is not None else []
