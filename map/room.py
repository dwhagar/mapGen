import random
from .item import Item
from .object import MapObject
from .encounter import Encounter

class Room:
    def __init__(self, identifier, blocks=None, color=None):
        self.identifier = identifier
        self.blocks = blocks if blocks is not None else []
        self.color = color

    def decorate(self):
        """
        Places items, objects, and encounters within the room based on its size.
        """
        max_decorations = len(self.blocks) // 9
        if max_decorations == 0:
            return

        num_to_place = random.randint(0, max_decorations)
        if num_to_place == 0:
            return
        
        unoccupied_blocks = [b for b in self.blocks if not b.contents]
        
        for _ in range(num_to_place):
            if not unoccupied_blocks:
                break

            chosen_block = random.choice(unoccupied_blocks)
            
            decoration_type = random.choice(['item', 'object', 'encounter'])

            if decoration_type == 'item':
                new_item = Item(room_identifier=self.identifier, block_location=chosen_block.location, description="A random item.")
                chosen_block.contents.append(new_item)
            
            elif decoration_type == 'object':
                obj_type = random.choice(list(range(17)))
                new_obj = MapObject(object_type=obj_type, room_identifier=self.identifier, block_locations=[chosen_block.location], description="A map object.")
                chosen_block.contents.append(new_obj)

            elif decoration_type == 'encounter':
                enc_type = random.choice(list(range(4)))
                new_enc = Encounter(encounter_type=enc_type, room_identifier=self.identifier, block_location=chosen_block.location, description="A random encounter.")
                chosen_block.contents.append(new_enc)
            
            unoccupied_blocks.remove(chosen_block)
