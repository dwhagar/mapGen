import random
import uuid
from .item import Item
from .object import MapObject
from .encounter import Encounter
from .stairs import Stairs
from .passage import Passage
from .constants import (ROOM_ITEM_CHANCE, ROOM_ENCOUNTER_CHANCE, ROOM_OBJECT_CHANCE, ENCOUNTER_TYPE_SWARM, OBJECT_TYPE_STAIRS_UP, OBJECT_TYPE_STAIRS_DOWN)
from .utils import get_random_item_type, get_random_encounter_type, get_random_object_type, get_center_of_blocks
from .text import ITEM_ADJECTIVES, ITEM_NOUNS, ITEM_DESCRIPTIONS, OBJECT_ADJECTIVES, OBJECT_NOUNS, OBJECT_DESCRIPTIONS, ENCOUNTER_PREFIXES, ENCOUNTER_NOUNS, ENCOUNTER_ACTIONS

class Room:
    """
    Represents a room on the map.
    """
    def __init__(self, identifier, blocks=None, color=None):
        """
        Initializes a Room.

        :param identifier: A unique string identifier (e.g., "R1").
        :param blocks: A list of Block objects that make up the room.
        :param color: The color to use when drawing this room.
        """
        self.identifier = identifier
        self.unique_id = uuid.uuid4()
        self.blocks = blocks if blocks is not None else []
        self.color = color
        self.contents = []

    def rename(self, new_identifier):
        """
        Renames the room.

        :param new_identifier: The new identifier for the room.
        """
        self.identifier = new_identifier

    def get_relative_position(self, obj_location, center):
        """
        Determines the relative position of an object compared to the center of the room.
        """
        dx = obj_location.x - center[0]
        dy = obj_location.y - center[1]

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

    def count_passages(self, map_instance):
        """
        Counts the number of passages connected to this room.

        :param map_instance: The map instance.
        :return: The number of passages connected to this room.
        """
        passage_count = 0
        for passage in map_instance.passages:
            if passage.side1.area_uid == self.unique_id or passage.side2.area_uid == self.unique_id:
                passage_count += 1
        return passage_count

    def decorate(self, map_instance, forced_object=None):
        """
        Places items, objects, and encounters within the room based on its size and probabilities.
        """
        if forced_object:
            obj_type, (x, y) = forced_object
            chosen_block = next((b for b in self.blocks if b.location.x == x and b.location.y == y), None)
            if chosen_block:
                position = self.get_relative_position(chosen_block.location, get_center_of_blocks(self.blocks))
                if obj_type == OBJECT_TYPE_STAIRS_UP or obj_type == OBJECT_TYPE_STAIRS_DOWN:
                    direction = "up" if obj_type == OBJECT_TYPE_STAIRS_UP else "down"
                    new_content = Stairs(block_uid=chosen_block.unique_id, direction=direction, position=position)
                else:
                    adj = random.choice(OBJECT_ADJECTIVES)
                    noun = OBJECT_NOUNS[obj_type]
                    description = f"There is {adj} {noun} {position}."
                    new_content = MapObject(object_type=obj_type, block_uids=[chosen_block.unique_id], description=description)
                
                if new_content:
                    chosen_block.contents.append(new_content)
                    self.contents.append(new_content)
            return

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
                new_content = Item(block_uid=chosen_block.unique_id, description=description)
                
            elif roll < ROOM_ITEM_CHANCE + ROOM_ENCOUNTER_CHANCE:
                enc_type = get_random_encounter_type()
                noun = ENCOUNTER_NOUNS[enc_type]
                action = random.choice(ENCOUNTER_ACTIONS)
                if enc_type == ENCOUNTER_TYPE_SWARM:
                    description = f"A {noun} is {action}."
                else:
                    prefix = random.choice(ENCOUNTER_PREFIXES)
                    description = f"{prefix} {noun} are {action}."
                new_content = Encounter(encounter_type=enc_type, block_uid=chosen_block.unique_id, description=description)

            elif roll < ROOM_ITEM_CHANCE + ROOM_ENCOUNTER_CHANCE + ROOM_OBJECT_CHANCE:
                obj_type = get_random_object_type()
                position = self.get_relative_position(chosen_block.location, room_center)
                
                if obj_type == OBJECT_TYPE_STAIRS_UP or obj_type == OBJECT_TYPE_STAIRS_DOWN:
                    direction = "up" if obj_type == OBJECT_TYPE_STAIRS_UP else "down"
                    new_content = Stairs(block_uid=chosen_block.unique_id, direction=direction, position=position)
                else:
                    adj = random.choice(OBJECT_ADJECTIVES)
                    noun = OBJECT_NOUNS[obj_type]
                    description = f"There is {adj} {noun} {position}."
                    new_content = MapObject(object_type=obj_type, block_uids=[chosen_block.unique_id], description=description)

            if new_content:
                chosen_block.contents.append(new_content)
                self.contents.append(new_content)