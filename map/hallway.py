import random
import uuid
from .item import Item
from .encounter import Encounter
from .passage import Passage
from .constants import HALLWAY_ITEM_CHANCE, HALLWAY_ENCOUNTER_CHANCE, ENCOUNTER_TYPE_SWARM
from .utils import get_random_item_type, get_random_encounter_type
from .text import ITEM_ADJECTIVES, ITEM_NOUNS, ITEM_DESCRIPTIONS, ENCOUNTER_PREFIXES, ENCOUNTER_NOUNS, ENCOUNTER_ACTIONS

class Hallway:
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
        self.identifier = new_identifier

    def count_passages(self):
        passage_uids = set()
        for block in self.blocks:
            for direction in ['north', 'south', 'east', 'west']:
                passage = getattr(block, direction)
                if isinstance(passage, Passage) and passage.is_door:
                    passage_uids.add(passage.unique_id)
        return len(passage_uids)

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
                noun = ENCOUNTER_NOUNS[enc_type]
                action = random.choice(ENCOUNTER_ACTIONS)
                if enc_type == ENCOUNTER_TYPE_SWARM:
                    description = f"A {noun} is {action}."
                else:
                    prefix = random.choice(ENCOUNTER_PREFIXES)
                    description = f"{prefix} {noun} are {action}."
                new_content = Encounter(encounter_type=enc_type, block_uid=chosen_block.unique_id, description=description)
            
            if new_content:
                chosen_block.contents.append(new_content)
                self.contents.append(new_content)