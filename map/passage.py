import random
from .constants import (DOOR_STATUS_SECRET, DOOR_STATUS_TRAPPED, DOOR_STATUS_LOCKED, DOOR_STATUS_CLOSED, DOOR_STATUS_OPEN,
                        DOOR_PROB_SECRET, DOOR_PROB_TRAPPED, DOOR_PROB_OPEN, DOOR_PROB_LOCKED)

class Door:
    def __init__(self):
        """
        Initializes a Door, automatically determining its type and status
        based on weighted probabilities.
        """
        door_type_roll = random.random()
        
        if door_type_roll < DOOR_PROB_SECRET:
            self.status = DOOR_STATUS_SECRET
        elif door_type_roll < DOOR_PROB_SECRET + DOOR_PROB_TRAPPED:
            self.status = DOOR_STATUS_TRAPPED
        else:
            state_roll = random.random()
            if state_roll < DOOR_PROB_OPEN:
                self.status = DOOR_STATUS_OPEN
            else:
                self.status = DOOR_STATUS_CLOSED
                if random.random() < DOOR_PROB_LOCKED:
                    self.status = DOOR_STATUS_LOCKED

class Passage:
    def __init__(self, side1=None, side2=None, is_door=False):
        self.side1 = side1
        self.side2 = side2
        self.is_door = is_door
        self.orientation = None  # 'horizontal' or 'vertical'
        
        if is_door:
            self.content = Door()
        else:
            self.content = None

    @property
    def door_status(self):
        if self.is_door and self.content:
            return self.content.status
        return None
