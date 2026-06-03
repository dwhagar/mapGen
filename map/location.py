"""
This module defines the Location class.
"""

class Location:
    """
    Represents a simple coordinate pair (x, y) on the map grid.
    """
    def __init__(self, x, y):
        """
        Initializes a Location instance.

        :param x: The x-coordinate.
        :param y: The y-coordinate.
        """
        self.x = x
        self.y = y
