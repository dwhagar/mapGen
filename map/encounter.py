"""
This module defines the Encounter class, a type of map content that represents
a potential challenge or interaction for players, such as monsters.
"""
import random
from .item import Item
from .text import ENCOUNTER_PREFIXES, ENCOUNTER_NOUNS, ENCOUNTER_ACTIONS

class Encounter(Item):
    """
    Represents an encounter on the map, such as a group of monsters.

    An Encounter is a specialized type of Item that generates a descriptive text
    for a potential confrontation. It can create random descriptions based on
    pre-defined text components.
    """
    def __init__(self, encounter_type, block_uid=None, description=None):
        """
        Initializes an Encounter instance.

        If a description is not provided, a random one will be generated based
        on the encounter type.

        :param encounter_type: The type of the encounter (e.g., 'monster'), which
                               determines the vocabulary for description generation.
        :param block_uid: The unique ID of the block where this encounter is located.
        :param description: A specific text description of the encounter. If None,
                            a random description is generated.
        """
        super().__init__(block_uid, description)
        self.encounter_type = encounter_type
        if not self.description:
            self.description = self._generate_random_description()

    def _generate_random_description(self):
        """
        Generates a random, descriptive sentence for the encounter.

        The description is composed of a prefix, a noun, and an action, with
        singular or plural forms chosen randomly. For example:
        "A lone goblin stands guard." or "Several skeletons are lurking in the shadows."

        :return: A randomly generated string describing the encounter.
        """
        # Randomly decide between a singular or plural encounter
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
        """
        Gets the icon representation for the encounter.

        :return: A string character to represent an encounter on the map.
        """
        return "★"
