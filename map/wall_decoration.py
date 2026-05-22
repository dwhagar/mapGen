class WallDecoration:
    """
    Represents a decoration applied to a segment of a wall.
    A wall segment is a continuous, straight line of walls.
    """
    def __init__(self, locations, direction, description, area_uid):
        """
        Initializes a WallDecoration.

        :param locations: A list of (x, y) tuples for the blocks forming the wall segment.
        :param direction: The direction of the wall relative to the blocks (e.g., 'north').
        :param description: The text description of the decoration.
        :param area_uid: The unique ID of the area this decoration is in.
        """
        self.locations = locations
        self.direction = direction
        self.description = description
        self.area_uid = area_uid