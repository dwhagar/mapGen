from .item import Item

class Encounter(Item):
    def __init__(self, encounter_type, block_uid=None, description=None):
        """
        Initializes an Encounter, which represents a potential confrontation for the players.

        :param encounter_type: The type of the encounter, using one of the ENCOUNTER_TYPE constants.
        :param block_uid: The unique ID of the block where this encounter is located.
        :param description: A text description of the encounter.
        """
        super().__init__(block_uid, description)
        self.encounter_type = encounter_type

    def get_icon(self):
        return "★"