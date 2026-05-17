# Door status constants
DOOR_STATUS_SECRET = 0
DOOR_STATUS_TRAPPED = 1
DOOR_STATUS_LOCKED = 2
DOOR_STATUS_CLOSED = 3
DOOR_STATUS_OPEN = 4

class Door:
    def __init__(self, status=DOOR_STATUS_CLOSED):
        self.status = status

class Passage:
    def __init__(self, side1=None, side2=None, is_door=False, door_status=DOOR_STATUS_CLOSED):
        self.side1 = side1
        self.side2 = side2
        if is_door:
            self.content = Door(door_status)
        else:
            self.content = None
