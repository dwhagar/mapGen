"""
This module defines the Room class, which represents a significant area on the map,
composed of multiple blocks. It handles the decoration of the room with various contents.
"""
import random
from .area import Area
from .item import Item
from .object import MapObject
from .encounter import Encounter
from .stairs import Stairs
from .constants import (ROOM_ITEM_CHANCE, ROOM_ENCOUNTER_CHANCE, ROOM_OBJECT_CHANCE, 
                        OBJECT_TYPE_STAIRS_UP, OBJECT_TYPE_STAIRS_DOWN, BLOCKS_PER_CONTENT_SLOT)
from .utils import get_random_item_type, get_random_encounter_type, get_random_object_type, get_center_of_blocks, get_relative_direction_from_center
from .text import ITEM_ADJECTIVES, ITEM_NOUNS, ITEM_DESCRIPTIONS, OBJECT_ADJECTIVES, OBJECT_NOUNS, OBJECT_DESCRIPTIONS

def decorate_rooms(the_map, add_objects):
    """
    Decorates all rooms on the map with items, objects, and encounters.
    Handles both randomly placed content and user-specified forced objects.
    """
    print("Decorating rooms...")
    
    forced_objects_with_loc = [obj for obj in add_objects if obj[1] is not None and obj[2] is not None]
    forced_objects_no_loc = [obj for obj in add_objects if obj[1] is None and obj[2] is None]

    rooms_with_forced_objects = set()

    # Place objects with specific locations first.
    for obj_type, x, y in forced_objects_with_loc:
        area = the_map.get_area_by_location(x, y)
        if area and isinstance(area, Room):
            area.decorate(the_map, forced_object=(obj_type, (x, y)))
            rooms_with_forced_objects.add(area.unique_id)

    # Place objects without specific locations in random available rooms.
    available_rooms = [room for room in the_map.rooms if room.unique_id not in rooms_with_forced_objects]
    random.shuffle(available_rooms)

    for obj_type, _, _ in forced_objects_no_loc:
        if available_rooms:
            room = available_rooms.pop()
            room.decorate(the_map, forced_object=(obj_type, None))
            rooms_with_forced_objects.add(room.unique_id)
        else:
            print(f"Warning: No available rooms to place object of type {obj_type}.")

    # Decorate the remaining rooms randomly.
    for room in the_map.rooms:
        if room.unique_id not in rooms_with_forced_objects:
            room.decorate(the_map)

class Room(Area):
    """
    Represents a room on the map, a collection of blocks forming a distinct area.

    Rooms are one of the primary area types in the map generation. They have an identifier,
    a set of blocks, and can be decorated with items, objects, and encounters.
    """
    def __init__(self, identifier, blocks=None, color=None):
        """
        Initializes a Room instance.

        :param identifier: A unique string identifier for the room (e.g., "R1").
        :param blocks: A list of Block objects that make up the room's area.
        :param color: The color to use when drawing this room on the PDF map.
        """
        super().__init__(identifier, blocks, color)

    def get_relative_position(self, obj_location, center):
        """
        Determines the relative position of an object within the room.

        This is used to generate more descriptive text, such as "in the northern part of the room".

        :param obj_location: The Location object of the content.
        :param center: A tuple (x, y) representing the center of the room.
        :return: A string describing the object's relative position.
        """
        direction = get_relative_direction_from_center([obj_location], center)
        if direction == "central":
            return "in the center of the room"
        return f"in the {direction} part of the room"

    def _create_item(self, block):
        """Factory method to create a random item in a given block."""
        item_type = get_random_item_type()
        adj = random.choice(ITEM_ADJECTIVES)
        noun = ITEM_NOUNS[item_type]
        desc = random.choice(ITEM_DESCRIPTIONS)
        description = f"You see {adj} {noun} {desc}."
        return Item(block_uid=block.unique_id, description=description)

    def _create_encounter(self, block):
        """Factory method to create a random encounter in a given block."""
        enc_type = get_random_encounter_type()
        return Encounter(encounter_type=enc_type, block_uid=block.unique_id)

    def _create_map_object(self, block, room_center, obj_type=None):
        """Factory method to create a random map object in a given block."""
        if obj_type is None:
            obj_type = get_random_object_type()
        position = self.get_relative_position(block.location, room_center)

        if obj_type in [OBJECT_TYPE_STAIRS_UP, OBJECT_TYPE_STAIRS_DOWN]:
            direction = "up" if obj_type == OBJECT_TYPE_STAIRS_UP else "down"
            return Stairs(block_uid=block.unique_id, direction=direction, position=position)
        else:
            adj = random.choice(OBJECT_ADJECTIVES)
            noun = OBJECT_NOUNS[obj_type]
            description = f"There is {adj} {noun} {position}."
            return MapObject(object_type=obj_type, block_uids=[block.unique_id], description=description)

    def decorate(self, map_instance, forced_object=None):
        """
        Populates the room with content like items, objects, and encounters.

        The number of content "slots" is determined by the room's size. The method then
        fills these slots based on probabilities defined in constants. It can also
        force the placement of a specific object.

        :param map_instance: The main map object.
        :param forced_object: An optional tuple (object_type, location) to force the
                              placement of a specific object.
        """
        if forced_object:
            obj_type, location = forced_object
            chosen_block = None
            if location:
                x, y = location
                # Find the specific block if location is provided
                chosen_block = next((b for b in self.blocks if b.location.x == x and b.location.y == y), None)
            else:
                # Otherwise, choose a random unoccupied block
                unoccupied_blocks = [b for b in self.blocks if not b.contents]
                if unoccupied_blocks:
                    chosen_block = random.choice(unoccupied_blocks)

            if chosen_block:
                new_content = self._create_map_object(chosen_block, get_center_of_blocks(self.blocks), obj_type=obj_type)
                if new_content:
                    chosen_block.contents.append(new_content)
                    self.contents.append(new_content)
            return

        # Determine the number of content slots based on room size
        num_slots = len(self.blocks) // BLOCKS_PER_CONTENT_SLOT
        if num_slots == 0:
            return

        unoccupied_blocks = [b for b in self.blocks if not b.contents]
        random.shuffle(unoccupied_blocks)
        
        room_center = get_center_of_blocks(self.blocks)

        # Define content generators with their respective chances
        content_generators = [
            (ROOM_ITEM_CHANCE, self._create_item),
            (ROOM_ENCOUNTER_CHANCE, self._create_encounter),
            (ROOM_OBJECT_CHANCE, self._create_map_object)
        ]

        # Fill the slots with content
        for _ in range(num_slots):
            if not unoccupied_blocks:
                break

            chosen_block = unoccupied_blocks.pop()
            
            # Use a weighted random roll to decide what content to generate
            roll = random.random()
            cumulative_chance = 0
            new_content = None

            for chance, generator_func in content_generators:
                cumulative_chance += chance
                if roll < cumulative_chance:
                    # Pass room_center only to the object generator
                    if generator_func == self._create_map_object:
                        new_content = generator_func(chosen_block, room_center)
                    else:
                        new_content = generator_func(chosen_block)
                    break

            if new_content:
                chosen_block.contents.append(new_content)
                self.contents.append(new_content)