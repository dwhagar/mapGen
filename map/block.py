from .passage import Passage
from .wall import Wall

class Block:
    def __init__(self, north=None, east=None, south=None, west=None, contents=None, floor=None, room_identifier=None, location=None):
        self.north = north
        self.east = east
        self.south = south
        self.west = west
        self.contents = contents if contents is not None else []
        self.floor = floor
        self.room_identifier = room_identifier
        self.location = location

    def check_adjacent(self, map_instance):
        """
        Checks adjacent blocks and creates walls or passages accordingly.
        This simplified version only builds walls between different zones.
        """
        x, y = self.location
        directions = {
            'north': (x, y - 1),
            'east': (x + 1, y),
            'south': (x, y + 1),
            'west': (x - 1, y)
        }

        for direction, (nx, ny) in directions.items():
            if getattr(self, direction) is None:
                neighbor = map_instance.get_block_at(nx, ny)
                
                if neighbor:
                    if self.room_identifier != neighbor.room_identifier:
                        # Boundary between different areas - always a wall for now.
                        wall = Wall()
                        setattr(self, direction, wall)
                        opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
                        setattr(neighbor, opposite[direction], wall)
                    else:
                        # Internal connection within the same area
                        passage = Passage(side1=self, side2=neighbor)
                        setattr(self, direction, passage)
                        opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
                        setattr(neighbor, opposite[direction], passage)
                else:
                    # Exterior wall
                    setattr(self, direction, Wall())
