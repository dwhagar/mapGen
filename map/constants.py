"""
This module defines global constants used throughout the map generation process.

It includes type identifiers, probability settings for various map features,
and configuration values for PDF output. Centralizing these constants makes
it easier to tune the behavior of the map generator.
"""

# --- TYPE CONSTANTS ---
# These constants provide a clear and consistent way to identify different types
# of objects, items, and encounters within the code.

# Object type constants
OBJECT_TYPE_TRAP = 0
OBJECT_TYPE_STATUE = 1
OBJECT_TYPE_FOUNTAIN = 2
OBJECT_TYPE_STAIRS_UP = 3
OBJECT_TYPE_STAIRS_DOWN = 4
OBJECT_TYPE_RUBBLE = 5
OBJECT_TYPE_PILLAR = 6
OBJECT_TYPE_ALTAR = 7
OBJECT_TYPE_THRONE = 8
OBJECT_TYPE_CHEST = 9
OBJECT_TYPE_LEVER = 10
OBJECT_TYPE_BUTTON = 11
OBJECT_TYPE_CHAIR = 12
OBJECT_TYPE_DEAD_BODY = 13
OBJECT_TYPE_TABLE = 14
OBJECT_TYPE_BED = 15
OBJECT_TYPE_POOL = 16

# Item type constants
ITEM_TYPE_POTION = 0
ITEM_TYPE_SCROLL = 1
ITEM_TYPE_WEAPON = 2
ITEM_TYPE_ARMOR = 3
ITEM_TYPE_GOLD = 4

# Encounter type constants
ENCOUNTER_TYPE_MONSTER = 0
ENCOUNTER_TYPE_ANIMAL = 1
ENCOUNTER_TYPE_UNDEAD = 2
ENCOUNTER_TYPE_SWARM = 3

# --- PROBABILITY CONSTANTS ---
# These values control the likelihood of various features appearing during map generation.
# They can be adjusted to change the density and type of content in the generated maps.

# Passage probabilities
PASSAGE_CREATION_CHANCE = 0.2  # The base chance a passage is created between adjacent areas.
PASSAGE_PROB_DOOR = 0.2       # Chance a passage becomes a door.
PASSAGE_PROB_SECRET = 0.1     # Chance a door is secret.
PASSAGE_PROB_TRAPPED = 0.1    # Chance a door is trapped.
PASSAGE_PROB_LOCKED = 0.1     # Chance a door is locked.
PASSAGE_PROB_OPEN = 0.1       # Chance a door is open.

# Map Object probabilities (relative probabilities for choosing a specific object type)
OBJECT_PROB_TRAP = 0.1
OBJECT_PROB_STATUE = 0.05
OBJECT_PROB_FOUNTAIN = 0.05
OBJECT_PROB_STAIRS_UP = 0.02
OBJECT_PROB_STAIRS_DOWN = 0.02
OBJECT_PROB_RUBBLE = 0.15
OBJECT_PROB_PILLAR = 0.1
OBJECT_PROB_ALTAR = 0.05
OBJECT_PROB_THRONE = 0.03
OBJECT_PROB_CHEST = 0.1
OBJECT_PROB_LEVER = 0.05
OBJECT_PROB_BUTTON = 0.05
OBJECT_PROB_CHAIR = 0.08
OBJECT_PROB_DEAD_BODY = 0.05
OBJECT_PROB_TABLE = 0.05
OBJECT_PROB_BED = 0.03
OBJECT_PROB_POOL = 0.02

# Item probabilities (relative probabilities for choosing a specific item type)
ITEM_PROB_POTION = 0.2
ITEM_PROB_SCROLL = 0.2
ITEM_PROB_WEAPON = 0.15
ITEM_PROB_ARMOR = 0.15
ITEM_PROB_GOLD = 0.3

# Encounter probabilities (relative probabilities for choosing a specific encounter type)
ENCOUNTER_PROB_MONSTER = 0.6
ENCOUNTER_PROB_ANIMAL = 0.3
ENCOUNTER_PROB_UNDEAD = 0.4
ENCOUNTER_PROB_SWARM = 0.2

# --- GLOBAL DECORATION PROBABILITY CONSTANTS ---
# These constants control the overall chance of adding content to rooms, hallways, and walls.

# For Rooms:
ROOM_OBJECT_CHANCE = 0.4      # The chance a room will contain at least one object.
ROOM_ENCOUNTER_CHANCE = 0.4   # The chance a room will contain an encounter.
ROOM_ITEM_CHANCE = 0.1        # The chance a room will contain an item.
BLOCKS_PER_CONTENT_SLOT = 9   # For every N blocks in a room, one content slot is available.

# For Hallways:
HALLWAY_ITEM_CHANCE = 0.05        # The chance a hallway will contain an item.
HALLWAY_ENCOUNTER_CHANCE = 0.2    # The chance a hallway will contain an encounter.
HALLWAY_OBSTACLE_COST = 100       # A high cost used in pathfinding to discourage paths through obstacles.

# For Walls:
WALL_DECORATION_CHANCE = 0.1  # The chance a wall segment will have a decoration.

# --- PDF GENERATION CONSTANTS ---
# These constants define the visual layout of the generated PDF map.

PDF_BLOCK_SIZE_MM = 6.35              # The size of one map block in millimeters (equivalent to 1/4 inch).
PDF_LEGEND_VERTICAL_SPACING = 30      # Vertical space used by the legend title.
PDF_LEGEND_HORIZONTAL_SPACING = 10    # Horizontal space between a legend symbol and its label.
