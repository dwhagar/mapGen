from .passage import Passage

class Location:
    """
    Represents a location on the map.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Area(Location):
    """
    Represents an area on the map, such as a room or a hallway.
    """
    def __init__(self, identifier, blocks=None, color=None):
        super().__init__(x=0, y=0)
        self.identifier = identifier
        self.blocks = blocks if blocks is not None else []
        self.unique_id = f"{self.identifier}-{id(self)}"
        self.color = color

    def __str__(self):
        return self.identifier

    def count_passages(self, map_instance):
        """
        Counts the number of passages connected to this area.
        """
        passage_uids = set()
        for block in self.blocks:
            for direction in ['north', 'south', 'east', 'west']:
                connection = getattr(block, direction)
                if isinstance(connection, Passage):
                    # Ensure the passage leads out of the current area
                    if connection.side1.area_uid != self.unique_id or connection.side2.area_uid != self.unique_id:
                        passage_uids.add(connection.unique_id)
        return len(passage_uids)

    def rename(self, new_identifier):
        self.identifier = new_identifier
        self.unique_id = f"{self.identifier}-{id(self)}"