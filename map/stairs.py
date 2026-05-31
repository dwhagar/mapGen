import random
from .object import MapObject
from .text import OBJECT_NOUNS
from .constants import OBJECT_TYPE_STAIRS_UP, OBJECT_TYPE_STAIRS_DOWN

class Stairs(MapObject):
    def __init__(self, block_uid, direction=None, position=""):
        if direction is None:
            direction = random.choice(["up", "down"])
        if direction not in ["up", "down"]:
            raise ValueError("Direction must be 'up' or 'down'")
        self.direction = direction
        
        object_type = OBJECT_TYPE_STAIRS_UP if self.direction == "up" else OBJECT_TYPE_STAIRS_DOWN
        description = f"There is a {OBJECT_NOUNS[object_type]} {position}."
        super().__init__(object_type, [block_uid], description)

    def get_icon(self):
        return "▲" if self.direction == "up" else "▼"

    def set_direction(self, direction):
        if direction not in ["up", "down"]:
            raise ValueError("Direction must be 'up' or 'down'")
        self.direction = direction
        # Update description when direction changes
        position = self.description.split(" ")[-1] # cheap way to get position back
        object_type = OBJECT_TYPE_STAIRS_UP if self.direction == "up" else OBJECT_TYPE_STAIRS_DOWN
        self.description = f"There is a {OBJECT_NOUNS[object_type]} {position}."