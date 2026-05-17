from .item import Item

# Encounter type constants
ENCOUNTER_TYPE_MONSTER = 0
ENCOUNTER_TYPE_ANIMAL = 1
ENCOUNTER_TYPE_UNDEAD = 2
ENCOUNTER_TYPE_SWARM = 3


class Encounter(Item):
    def __init__(self, encounter_type, room_identifier=None, block_location=None, description=None):
        """
        Initializes an Encounter, which represents a potential confrontation for the players.

        :param encounter_type: The type of the encounter, using one of the ENCOUNTER_TYPE constants.
        :param room_identifier: The identifier of the room this encounter is in.
        :param block_location: The (x, y) coordinates of the block where this encounter is located.
        :param description: A text description of the encounter.
        """
        super().__init__(room_identifier, block_location, description)
        self.encounter_type = encounter_type
