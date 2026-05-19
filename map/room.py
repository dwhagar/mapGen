import random
from .item import Item
from .object import MapObject
from .encounter import Encounter
from .constants import (ROOM_ITEM_CHANCE, ROOM_ENCOUNTER_CHANCE, ROOM_OBJECT_CHANCE, ENCOUNTER_TYPE_SWARM)
from .utils import get_random_item_type, get_random_encounter_type, get_random_object_type, get_center_of_blocks
from .text import ITEM_ADJECTIVES, ITEM_NOUNS, ITEM_DESCRIPTIONS, OBJECT_ADJECTIVES, OBJECT_NOUNS, OBJECT_DESCRIPTIONS, ENCOUNTER_PREFIXES, ENCOUNTER_NOUNS, ENCOUNTER_ACTIONS

class Room:
    def __init__(self, identifier, blocks=None, color=None):
        self.identifier = identifier
        self.blocks = blocks if blocks is not None else []
        self.color = color
        self.contents = []

    def rename(self, new_identifier):
        self.identifier = new_identifier
        for block in self.blocks:
            block.room_identifier = new_identifier
            for content in block.contents:
                content.room_identifier = new_identifier

    def get_relative_position(self, obj_location, center):
        """
        Determines the relative position of an object compared to the center of the room.
        """
        dx = obj_location[0] - center[0]
        dy = obj_location[1] - center[1]

        if abs(dx) < 2 and abs(dy) < 2:
            return "in the center of the room"
        
        if dy > abs(dx):
            return "in the northern part of the room"
        elif dy < -abs(dx):
            return "in the southern part of the room"
        elif dx > abs(dy):
            return "in the eastern part of the room"
        else: # dx < -abs(dy)
            return "in the western part of the room"

    def decorate(self):
        """
        Places items, objects, and encounters within the room based on its size and probabilities.
        """
        num_slots = len(self.blocks) // 9
        if num_slots == 0:
            return

        unoccupied_blocks = [b for b in self.blocks if not b.contents]
        random.shuffle(unoccupied_blocks)
        
        room_center = get_center_of_blocks(self.blocks)

        for _ in range(num_slots):
            if not unoccupied_blocks:
                break

            roll = random.random()
            chosen_block = unoccupied_blocks.pop()

            new_content = None
            if roll < ROOM_ITEM_CHANCE:
                item_type = get_random_item_type()
                adj = random.choice(ITEM_ADJECTIVES)
                noun = ITEM_NOUNS[item_type]
                desc = random.choice(ITEM_DESCRIPTIONS)
                description = f"You see {adj} {noun} {desc}."
                new_content = Item(room_identifier=self.identifier, block_location=chosen_block.location, description=description)
                
            elif roll < ROOM_ITEM_CHANCE + ROOM_ENCOUNTER_CHANCE:
                enc_type = get_random_encounter_type()
                noun = ENCOUNTER_NOUNS[enc_type]
                action = random.choice(ENCOUNTER_ACTIONS)
                if enc_type == ENCOUNTER_TYPE_SWARM:
                    description = f"A {noun} is {action}."
                else:
                    prefix = random.choice(ENCOUNTER_PREFIXES)
                    description = f"{prefix} {noun} are {action}."
                new_content = Encounter(encounter_type=enc_type, room_identifier=self.identifier, block_location=chosen_block.location, description=description)

            elif roll < ROOM_ITEM_CHANCE + ROOM_ENCOUNTER_CHANCE + ROOM_OBJECT_CHANCE:
                obj_type = get_random_object_type()
                adj = random.choice(OBJECT_ADJECTIVES)
                noun = OBJECT_NOUNS[obj_type]
                position = self.get_relative_position(chosen_block.location, room_center)
                description = f"There is {adj} {noun} {position}."
                new_content = MapObject(object_type=obj_type, room_identifier=self.identifier, block_locations=[chosen_block.location], description=description)

            if new_content:
                chosen_block.contents.append(new_content)
                self.contents.append(new_content)