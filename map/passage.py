import random

# Door status constants
DOOR_STATUS_SECRET = 0
DOOR_STATUS_TRAPPED = 1
DOOR_STATUS_LOCKED = 2
DOOR_STATUS_CLOSED = 3
DOOR_STATUS_OPEN = 4

class Door:
    def __init__(self):
        """
        Initializes a Door, automatically determining its type and status
        based on weighted probabilities.
        """
        door_type_roll = random.random()
        
        if door_type_roll < 0.1:  # 10% chance of a secret door
            self.status = DOOR_STATUS_SECRET
        elif door_type_roll < 0.2:  # 10% chance of a trapped door
            self.status = DOOR_STATUS_TRAPPED
        else:  # 80% chance of a regular door
            state_roll = random.random()
            if state_roll < 0.2:  # 20% chance of being open
                self.status = DOOR_STATUS_OPEN
            else:  # 80% chance of being closed
                self.status = DOOR_STATUS_CLOSED
                if random.random() < 0.25:  # 25% of closed doors are locked
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
