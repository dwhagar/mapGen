import random
import uuid
from .item import Item
from .encounter import Encounter
from .passage import Passage
from .constants import HALLWAY_ITEM_CHANCE, HALLWAY_ENCOUNTER_CHANCE
from .utils import get_random_item_type, get_random_encounter_type
from .text import ITEM_ADJECTIVES, ITEM_NOUNS, ITEM_DESCRIPTIONS

class Hallway:
    """
    Represents a hallway on the map.
    """
    def __init__(self, identifier, connects_rooms=None, blocks=None, width=1, color=None):
        """
        Initializes a Hallway, which is a collection of blocks connecting two rooms.

        :param identifier: A unique string identifier (e.g., "H1").
        :param connects_rooms: A tuple containing the unique_ids of the two rooms it connects.
        :param blocks: A list of Block objects that make up the hallway.
        :param width: The width of the hallway in blocks (e.g., 1 or 2).
        :param color: The color to use when drawing this hallway.
        """
        self.identifier = identifier
        self.unique_id = uuid.uuid4()
        self.connects_rooms = connects_rooms if connects_rooms is not None else (None, None)
        self.blocks = blocks if blocks is not None else []
        self.width = width
        self.color = color
        self.contents = []

    def rename(self, new_identifier):
        """
        Renames the hallway.

        :param new_identifier: The new identifier for the hallway.
        """
        self.identifier = new_identifier

    def count_passages(self, map_instance):
        """
        Counts the number of passages connected to this hallway.

        :param map_instance: The map instance.
        :return: The number of passages connected to this hallway.
        """
        passage_count = 0
        for passage in map_instance.passages:
            if passage.side1.area_uid == self.unique_id or passage.side2.area_uid == self.unique_id:
                passage_count += 1
        return passage_count

    def decorate(self, map_instance):
        """
        Places items and encounters within the hallway based on its size and probabilities.
        Hallways cannot contain map objects.
        """
        num_slots = len(self.blocks) // 9
        if num_slots == 0:
            return

        unoccupied_blocks = [b for b in self.blocks if not b.contents]
        random.shuffle(unoccupied_blocks)

        for _ in range(num_slots):
            if not unoccupied_blocks:
                break

            roll = random.random()
            chosen_block = unoccupied_blocks.pop()

            new_content = None
            if roll < HALLWAY_ITEM_CHANCE:
                item_type = get_random_item_type()
                adj = random.choice(ITEM_ADJECTIVES)
                noun = ITEM_NOUNS[item_type]
                desc = random.choice(ITEM_DESCRIPTIONS)
                description = f"You see {adj} {noun} {desc}."
                new_content = Item(block_uid=chosen_block.unique_id, description=description)

            elif roll < HALLWAY_ITEM_CHANCE + HALLWAY_ENCOUNTER_CHANCE:
                enc_type = get_random_encounter_type()
                new_content = Encounter(encounter_type=enc_type, block_uid=chosen_block.unique_id)
            
            if new_content:
                chosen_block.contents.append(new_content)
                self.contents.append(new_content)