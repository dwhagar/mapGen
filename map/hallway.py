"""
This module defines the Hallway class, which represents a corridor connecting
different areas on the map.
"""
import random
from .area import Area
from .item import Item
from .encounter import Encounter
from .constants import HALLWAY_ITEM_CHANCE, HALLWAY_ENCOUNTER_CHANCE
from .utils import get_random_item_type, get_random_encounter_type
from .text import ITEM_ADJECTIVES, ITEM_NOUNS, ITEM_DESCRIPTIONS

def decorate_hallways(the_map):
    """
    Decorates all hallways on the map with items and encounters based on a set
    of probabilities. This function iterates through each hallway and calls its
    `decorate` method to add content.
    """
    print("Decorating hallways...")
    for hallway in the_map.hallways:
        hallway.decorate(the_map)

class Hallway(Area):
    """
    Represents a hallway on the map, which is a path of blocks connecting rooms.
    Hallways are essential for ensuring connectivity between different areas of the map.
    They can also contain their own content, such as items or encounters, though
    typically at a lower density than rooms.
    """
    def __init__(self, identifier, connects_rooms=None, blocks=None, width=1, color=None):
        """
        Initializes a Hallway instance.

        :param identifier: A unique string identifier for the hallway (e.g., "H1").
        :param connects_rooms: A tuple containing the unique_ids of the two rooms it connects.
        :param blocks: A list of Block objects that make up the hallway's path.
        :param width: The width of the hallway in blocks (typically 1).
        :param color: The color to use when drawing this hallway on the PDF map.
        """
        super().__init__(identifier, blocks, color)
        self.connects_rooms = connects_rooms if connects_rooms is not None else (None, None)
        self.width = width

    def decorate(self, the_map):
        """
        Populates the hallway with content like items and encounters. The number of
        content "slots" is determined by the hallway's length, and each slot has a
        chance to be filled with an item or an encounter based on predefined probabilities.
        
        :param the_map: The main map object, used to access global properties if needed.
        """
        # One content slot is available for every 9 blocks in the hallway.
        num_slots = len(self.blocks) // 9
        if num_slots == 0:
            return

        # Ensure content is placed only in unoccupied blocks.
        unoccupied_blocks = [b for b in self.blocks if not b.contents]
        random.shuffle(unoccupied_blocks)

        for _ in range(num_slots):
            if not unoccupied_blocks:
                break  # Stop if there are no more free blocks.

            roll = random.random()
            chosen_block = unoccupied_blocks.pop()

            new_content = None
            # Decide whether to place an item or an encounter.
            if roll < HALLWAY_ITEM_CHANCE:
                item_type = get_random_item_type()
                adj = random.choice(ITEM_ADJECTIVES)
                noun = ITEM_NOUNS.get(item_type, "item")
                desc = random.choice(ITEM_DESCRIPTIONS)
                description = f"You see {adj} {noun} {desc}."
                new_content = Item(block_uid=chosen_block.unique_id, description=description)

            elif roll < HALLWAY_ITEM_CHANCE + HALLWAY_ENCOUNTER_CHANCE:
                enc_type = get_random_encounter_type()
                new_content = Encounter(encounter_type=enc_type, block_uid=chosen_block.unique_id)
            
            if new_content:
                chosen_block.contents.append(new_content)
                self.contents.append(new_content)