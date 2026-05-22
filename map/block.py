import uuid
from .passage import Passage
from .wall import Wall

class Block:
    def __init__(self, area_uid=None, location=None, contents=None, floor=None):
        self.unique_id = uuid.uuid4()
        self.area_uid = area_uid
        self.location = location
        self.contents = contents if contents is not None else []
        self.floor = floor
        self.north = None
        self.east = None
        self.south = None
        self.west = None

    def get_area(self, map_instance):
        return map_instance.get_area_by_uid(self.area_uid)

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
                    if self.area_uid != neighbor.area_uid:
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