from .constants import (
    # Item types
    ITEM_TYPE_POTION,
    ITEM_TYPE_SCROLL,
    ITEM_TYPE_WEAPON,
    ITEM_TYPE_ARMOR,
    ITEM_TYPE_GOLD,
    # Object types
    OBJECT_TYPE_TRAP,
    OBJECT_TYPE_STATUE,
    OBJECT_TYPE_FOUNTAIN,
    OBJECT_TYPE_STAIRS_UP,
    OBJECT_TYPE_STAIRS_DOWN,
    OBJECT_TYPE_RUBBLE,
    OBJECT_TYPE_PILLAR,
    OBJECT_TYPE_ALTAR,
    OBJECT_TYPE_THRONE,
    OBJECT_TYPE_CHEST,
    OBJECT_TYPE_LEVER,
    OBJECT_TYPE_BUTTON,
    OBJECT_TYPE_CHAIR,
    OBJECT_TYPE_DEAD_BODY,
    OBJECT_TYPE_TABLE,
    OBJECT_TYPE_BED,
    OBJECT_TYPE_POOL,
    # Encounter types
    ENCOUNTER_TYPE_MONSTER,
    ENCOUNTER_TYPE_ANIMAL,
    ENCOUNTER_TYPE_UNDEAD,
    ENCOUNTER_TYPE_SWARM,
)

# Descriptions for Items
ITEM_ADJECTIVES = [
    "a dusty", "a rusty", "a gleaming", "an old", "a small", "a large", "a forgotten",
]
ITEM_NOUNS = {
    ITEM_TYPE_POTION: "potion",
    ITEM_TYPE_SCROLL: "scroll",
    ITEM_TYPE_WEAPON: "weapon",
    ITEM_TYPE_ARMOR: "suit of armor",
    ITEM_TYPE_GOLD: "pile of gold",
}
ITEM_DESCRIPTIONS = [
    "lying on the floor", "tucked into a corner", "propped against a wall", "shimmering faintly",
]

# Descriptions for Map Objects
OBJECT_ADJECTIVES = [
    "a sturdy", "a broken", "an ornate", "a simple", "a heavy", "a light",
]
OBJECT_NOUNS = {
    OBJECT_TYPE_TRAP: "trap",
    OBJECT_TYPE_STATUE: "statue",
    OBJECT_TYPE_FOUNTAIN: "fountain",
    OBJECT_TYPE_STAIRS_UP: "staircase going up",
    OBJECT_TYPE_STAIRS_DOWN: "staircase going down",
    OBJECT_TYPE_RUBBLE: "pile of rubble",
    OBJECT_TYPE_PILLAR: "pillar",
    OBJECT_TYPE_ALTAR: "altar",
    OBJECT_TYPE_THRONE: "throne",
    OBJECT_TYPE_CHEST: "chest",
    OBJECT_TYPE_LEVER: "lever",
    OBJECT_TYPE_BUTTON: "button",
    OBJECT_TYPE_CHAIR: "chair",
    OBJECT_TYPE_DEAD_BODY: "dead body",
    OBJECT_TYPE_TABLE: "table",
    OBJECT_TYPE_BED: "bed",
    OBJECT_TYPE_POOL: "pool of water",
}
OBJECT_DESCRIPTIONS = [
    "sitting in the middle of the room", "covered in cobwebs", "that looks recently used", "carved with strange symbols",
]

# Descriptions for Encounters
ENCOUNTER_PREFIXES = {
    "singular": ["A lone", "A menacing", "A strange"],
    "plural": ["A group of", "A pack of", "A cluster of"],
}
ENCOUNTER_NOUNS = {
    ENCOUNTER_TYPE_MONSTER: {"singular": "monster", "plural": "monsters"},
    ENCOUNTER_TYPE_ANIMAL: {"singular": "animal", "plural": "animals"},
    ENCOUNTER_TYPE_UNDEAD: {"singular": "undead creature", "plural": "undead creatures"},
    ENCOUNTER_TYPE_SWARM: {"singular": "swarm of vermin", "plural": "swarms of vermin"},
}
ENCOUNTER_ACTIONS = {
    "singular": ["is patrolling the area", "is sleeping soundly", "is standing guard", "is making strange noises", "is pacing back and forth", "is shuffling aimlessly"],
    "plural": ["are patrolling the area", "are sleeping soundly", "are standing guard", "are making strange noises", "are pacing back and forth", "are shuffling aimlessly"],
}

# Descriptions for Wall Decorations
WALL_DECORATIONS = [
    # Mundane & Common
    "a series of faded tapestries depicting a forgotten battle",
    "a row of empty, rusted torch sconces",
    "a collection of crude, faded paintings of previous inhabitants",
    "a long, deep crack that runs from floor to ceiling",
    "a thick layer of green moss and strange, phosphorescent fungi",
    "a set of heavy iron chains bolted to the wall, their purpose unknown",
    "a series of empty shelves, covered in dust",
    "a line of peeling, water-damaged frescoes",
    "a row of hooks, some still holding tattered bits of cloth",
    "a series of small, barred windows, now bricked over",
    "a large, dark stain that resembles a screaming face",
    "a collection of tally marks, scratched into the stone",

    # Strange & Eerie
    "a series of strange, glowing runes that pulse with a faint, sickly light",
    "a collection of mirrors that reflect a distorted, nightmarish version of the room",
    "a row of mounted animal heads, their eyes seeming to follow you",
    "a series of alcoves, each containing a small, unnerving doll",
    "a wall that seems to ripple and shift, as if it were made of liquid",
    "a collection of handprints, burned into the stone",
    "a series of carvings that depict a disturbing, ritualistic scene",
    "a wall that whispers incomprehensible secrets when you get close",
    "a collection of clocks, all stopped at the exact same time",
    "a series of faces, carved into the wall, their expressions a mixture of terror and ecstasy",
    "a wall that is unnaturally cold to the touch",

    # Magical & Fantastic
    "a series of glowing crystals, embedded in the wall, that cast a rainbow of colors",
    "a mural that slowly changes, depicting the rise and fall of a forgotten kingdom",
    "a series of portals, shimmering with an otherworldly energy, that seem to lead to unknown realms",
    "a wall that is covered in a sheet of ice, even in the warmest of rooms",
    "a collection of floating stones that orbit a central, glowing glyph",
    "a series of magical wards, still glowing with a faint, protective energy",
    "a wall that is made entirely of a strange, translucent material, revealing the rock and earth beyond",
    "a collection of ancient weapons, mounted on the wall, that seem to hum with a latent power",
    "a series of carvings that seem to move when you're not looking directly at them",
    "a wall that is covered in a living, breathing carpet of moss that gently sways",
]

TRAPPED_DOOR_DESCRIPTIONS = [
    "a faint, almost invisible tripwire stretched across the bottom of the doorframe",
    "a small, cleverly hidden dart hole in the adjacent wall",
    "a pressure plate under the floor just before the door",
    "a strange, sweet-smelling gas that hisses from a hidden nozzle",
    "a series of small, sharp spikes that spring from the doorframe",
    "a heavy block that falls from the ceiling above the door",
    "a magical glyph on the door that glows with a faint, menacing light",
    "a spring-loaded blade that sweeps across the doorway",
    "a pit that opens up in the floor just beyond the door",
    "a loud, piercing alarm that sounds when the door is opened",
]