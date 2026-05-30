import uuid

class Passage:
    """
    Represents a connection between two adjacent blocks on the map.
    A passage can be a simple opening or a door.
    """
    def __init__(self, side1=None, side2=None, is_door=False):
        """
        Initializes a Passage.

        :param side1: The first block connected by the passage.
        :param side2: The second block connected by the passage.
        :param is_door: A boolean indicating if the passage is a door.
        """
        self.unique_id = uuid.uuid4()
        self.side1 = side1
        self.side2 = side2
        self.is_door = is_door
        self.orientation = self._determine_orientation()

    def _determine_orientation(self):
        """
        Determines the orientation of the passage (horizontal or vertical).
        """
        if self.side1 and self.side2:
            if self.side1.location.x == self.side2.location.x:
                return 'vertical'
            elif self.side1.location.y == self.side2.location.y:
                return 'horizontal'
        return None