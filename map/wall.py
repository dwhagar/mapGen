"""
This module defines the Wall class, which represents a boundary between blocks.
"""

class Wall:
    """
    Represents a solid boundary between two blocks or at the edge of the map.

    A Wall object is used to signify an impassable barrier. It can also hold
    'contents', which could represent wall-mounted features or decorations.
    """
    def __init__(self, contents=None):
        """
        Initializes a new Wall instance.

        :param contents: A list of items or decorations attached to the wall.
                         For future use, e.g., for wall-mounted traps or features.
        """
        self.contents = contents if contents is not None else []
