class Block:
    def __init__(self, north=None, east=None, south=None, west=None, contents=None, floor=None):
        self.north = north
        self.east = east
        self.south = south
        self.west = west
        self.contents = contents if contents is not None else []
        self.floor = floor
