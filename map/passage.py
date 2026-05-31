import uuid

class Passage:
    """
    Represents a connection between two adjacent blocks on the map.
    A passage can be a simple opening, a door, a secret door, or a trapped door.
    """
    def __init__(self, side1=None, side2=None, is_door=False, is_secret=False, is_trapped=False, is_locked=False, is_open=False, description=None):
        """
        Initializes a Passage.

        :param side1: The first block connected by the passage.
        :param side2: The second block connected by the passage.
        :param is_door: A boolean indicating if the passage is a door.
        :param is_secret: A boolean indicating if the passage is secret.
        :param is_trapped: A boolean indicating if the passage is trapped.
        :param is_locked: A boolean indicating if the door is locked.
        :param is_open: A boolean indicating if the door is open.
        :param description: A description of the passage.
        """
        self.unique_id = uuid.uuid4()
        self.side1 = side1
        self.side2 = side2
        self.is_door = is_door
        self.is_secret = is_secret
        self.is_trapped = is_trapped
        self.is_locked = is_locked
        self.is_open = is_open
        self.description = description
        self.orientation = self._determine_orientation()

    def _determine_orientation(self):
        """
        Determines the orientation of the passage (horizontal or vertical).
        """
        if self.side1 and self.side2:
            if self.side1.location.x == self.side2.location.x:
                return 'horizontal'
            elif self.side1.location.y == self.side2.location.y:
                return 'vertical'
        return None