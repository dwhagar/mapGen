import random
from .item import Item
from .text import ENCOUNTER_PREFIXES, ENCOUNTER_NOUNS, ENCOUNTER_ACTIONS

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
        if not self.description:
            self.description = self._generate_random_description()

    def _generate_random_description(self):
        """
        Generates a random description for the encounter.
        """
        is_singular = random.random() < 0.5
        
        if is_singular:
            prefix = random.choice(ENCOUNTER_PREFIXES["singular"])
            noun = ENCOUNTER_NOUNS[self.encounter_type]["singular"]
            action = random.choice(ENCOUNTER_ACTIONS["singular"])
            return f"{prefix} {noun} {action}."
        else:
            prefix = random.choice(ENCOUNTER_PREFIXES["plural"])
            noun = ENCOUNTER_NOUNS[self.encounter_type]["plural"]
            action = random.choice(ENCOUNTER_ACTIONS["plural"])
            return f"{prefix} {noun} {action}."

    def get_icon(self):
        return "★"