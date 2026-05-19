import random
from .constants import *

def get_random_object_type():
    roll = random.random()
    if roll < OBJECT_PROB_TRAP:
        return OBJECT_TYPE_TRAP
    roll -= OBJECT_PROB_TRAP
    if roll < OBJECT_PROB_STATUE:
        return OBJECT_TYPE_STATUE
    roll -= OBJECT_PROB_STATUE
    if roll < OBJECT_PROB_FOUNTAIN:
        return OBJECT_TYPE_FOUNTAIN
    roll -= OBJECT_PROB_FOUNTAIN
    if roll < OBJECT_PROB_STAIRS_UP:
        return OBJECT_TYPE_STAIRS_UP
    roll -= OBJECT_PROB_STAIRS_UP
    if roll < OBJECT_PROB_STAIRS_DOWN:
        return OBJECT_TYPE_STAIRS_DOWN
    roll -= OBJECT_PROB_STAIRS_DOWN
    if roll < OBJECT_PROB_RUBBLE:
        return OBJECT_TYPE_RUBBLE
    roll -= OBJECT_PROB_RUBBLE
    if roll < OBJECT_PROB_PILLAR:
        return OBJECT_TYPE_PILLAR
    roll -= OBJECT_PROB_PILLAR
    if roll < OBJECT_PROB_ALTAR:
        return OBJECT_TYPE_ALTAR
    roll -= OBJECT_PROB_ALTAR
    if roll < OBJECT_PROB_THRONE:
        return OBJECT_TYPE_THRONE
    roll -= OBJECT_PROB_THRONE
    if roll < OBJECT_PROB_CHEST:
        return OBJECT_TYPE_CHEST
    roll -= OBJECT_PROB_CHEST
    if roll < OBJECT_PROB_LEVER:
        return OBJECT_TYPE_LEVER
    roll -= OBJECT_PROB_LEVER
    if roll < OBJECT_PROB_BUTTON:
        return OBJECT_TYPE_BUTTON
    roll -= OBJECT_PROB_BUTTON
    if roll < OBJECT_PROB_CHAIR:
        return OBJECT_TYPE_CHAIR
    roll -= OBJECT_PROB_CHAIR
    if roll < OBJECT_PROB_DEAD_BODY:
        return OBJECT_TYPE_DEAD_BODY
    roll -= OBJECT_PROB_DEAD_BODY
    if roll < OBJECT_PROB_TABLE:
        return OBJECT_TYPE_TABLE
    roll -= OBJECT_PROB_TABLE
    if roll < OBJECT_PROB_BED:
        return OBJECT_TYPE_BED
    # Default to POOL if nothing else hits, to account for float precision
    return OBJECT_TYPE_POOL

def get_random_item_type():
    roll = random.random()
    if roll < ITEM_PROB_POTION:
        return ITEM_TYPE_POTION
    roll -= ITEM_PROB_POTION
    if roll < ITEM_PROB_SCROLL:
        return ITEM_TYPE_SCROLL
    roll -= ITEM_PROB_SCROLL
    if roll < ITEM_PROB_WEAPON:
        return ITEM_TYPE_WEAPON
    roll -= ITEM_PROB_WEAPON
    if roll < ITEM_PROB_ARMOR:
        return ITEM_TYPE_ARMOR
    # Default to GOLD
    return ITEM_TYPE_GOLD

def get_random_encounter_type():
    roll = random.random()
    if roll < ENCOUNTER_PROB_MONSTER:
        return ENCOUNTER_TYPE_MONSTER
    roll -= ENCOUNTER_PROB_MONSTER
    if roll < ENCOUNTER_PROB_ANIMAL:
        return ENCOUNTER_TYPE_ANIMAL
    roll -= ENCOUNTER_PROB_ANIMAL
    if roll < ENCOUNTER_PROB_UNDEAD:
        return ENCOUNTER_TYPE_UNDEAD
    # Default to SWARM
    return ENCOUNTER_TYPE_SWARM

def get_center_of_blocks(blocks):
    if not blocks: return None
    x_coords = [b.location[0] for b in blocks]
    y_coords = [b.location[1] for b in blocks]
    return (sum(x_coords) // len(x_coords), sum(y_coords) // len(y_coords))
