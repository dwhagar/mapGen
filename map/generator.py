"""
This module contains the main Generator class, which is responsible for orchestrating
the entire procedural generation of the dungeon map.
"""
import random
from reportlab.lib.colors import Color

from .map import Map
from .room import Room, decorate_rooms
from .hallway import Hallway, decorate_hallways
from .block import Block
from .location import Location
from .wall import Wall
from .passage import Passage
from .wall_decoration import WallDecoration, decorate_walls
from .utils import get_center_of_blocks, is_area_free, is_safe_to_punch_passage
from .maze import generate_maze_layout
from .hallway_generator import generate_hallway_layout
from .constants import PASSAGE_CREATION_CHANCE, PASSAGE_PROB_DOOR, PASSAGE_PROB_SECRET, \
    PASSAGE_PROB_TRAPPED, PASSAGE_PROB_LOCKED, PASSAGE_PROB_OPEN


class Generator:
    """
    The main class for generating the dungeon map.
    This class orchestrates the entire map generation process, from initializing the grid
    to scattering rooms, creating connections, and ensuring the final map is coherent
    and fully connected.
    """
    def __init__(self, width=25, height=25, placement_retries=10, add_objects=None, maze_mode=False):
        """
        Initializes the map Generator.

        :param width: The width of the map grid.
        :param height: The height of the map grid.
        :param placement_retries: The number of times to attempt placing a room before giving up.
        :param add_objects: A list of specific objects to force into the map generation.
        :param maze_mode: If True, generate a maze; otherwise, use hallway connections.
        """
        self.map = Map(width, height)
        self.placement_retries = placement_retries
        self.hallway_count = 0
        self.add_objects = add_objects if add_objects else []
        self.default_color = Color(0.8, 0.8, 0.8)
        self.maze_mode = maze_mode

    def generate(self):
        """
        The main public method to generate and return a complete map.
        This method guides the generation process through several stages:
        1. Initialize the map with empty blocks.
        2. Scatter rooms across the map.
        3. Generate hallways or a maze to connect the rooms.
        4. Punch additional passages for more connectivity.
        5. Ensure the entire map is a single connected component.
        6. Decorate rooms, hallways, and walls.
        7. Renumber and validate the final map areas.
        """
        print(f"Starting map generation... (Mode: {'Maze' if self.maze_mode else 'Hallway'})")
        
        # 1. Initialize the map grid.
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                self.map.blocks[(x, y)] = Block(location=Location(x, y), empty=True)
        
        # 2. Scatter rooms.
        num_rooms = random.randint(self.map.MIN_ROOMS, self.map.MAX_ROOMS)
        print(f"Attempting to generate {num_rooms} rooms.")
        self._scatter_rooms(num_rooms)

        # 3. Generate connections (hallways or maze).
        if self.maze_mode:
            self.hallway_count = generate_maze_layout(self.map, self.hallway_count)
        else:
            self.hallway_count = generate_hallway_layout(self.map, self.hallway_count)

        # 4. Punch optional passages.
        self._punch_passages()
        
        # 5. Ensure full map connectivity.
        self._ensure_map_connectivity()
        
        # 6. Decorate the map.
        decorate_rooms(self.map, self.add_objects)
        decorate_hallways(self.map)
        decorate_walls(self.map)
        
        # 7. Finalize and validate.
        self._renumber_and_validate()
        
        print(f"Map generation complete with {len(self.map.rooms)} rooms and {len(self.map.hallways)} hallways.")
        return self.map

    def _place_single_room(self, room_identifier, room_min_x, room_min_y, room_width, room_height):
        """
        Places a single room on the map at a specified location.
        This function creates a new Room object, assigns blocks to it, and sets up
        the initial walls for the room.
        """
        if room_width * room_height < 1:  # A room must have at least one block.
            return False
            
        new_room = Room(identifier=room_identifier, color=self.default_color)
        blocks_for_room = []
        for y_offset in range(room_height):
            for x_offset in range(room_width):
                block = self.map.get_block_at(room_min_x + x_offset, room_min_y + y_offset)
                if not block:
                    # This should not happen if is_area_free is working correctly.
                    print(f"Error: Attempted to place a room in an invalid block at ({room_min_x + x_offset}, {room_min_y + y_offset}).")
                    return False
                block.area_uid = new_room.unique_id
                block.empty = False
                blocks_for_room.append(block)
        
        new_room.blocks = blocks_for_room
        for block in blocks_for_room:
            block._set_initial_walls(self.map)

        self.map.add_room(new_room)
        return True

    def _scatter_rooms(self, num_rooms):
        """
        Scatters a specified number of rooms across the map.
        This function also handles placing rooms for pre-defined objects.
        """
        print("Scattering rooms...")
        
        # First, place rooms for any pre-defined objects.
        for obj_data in self.add_objects:
            obj_type, x, y = obj_data
            if x is None or y is None:
                continue
            
            room_identifier = f"R{len(self.map.rooms) + 1}"
            placed = False
            for _ in range(self.placement_retries):
                room_width = random.randint(2, 5)
                room_height = random.randint(2, 5)
                # Center the room around the object's coordinates.
                room_min_x = x - random.randint(1, room_width - 1)
                room_min_y = y - random.randint(1, room_height - 1)
                
                if is_area_free(self.map, room_min_x, room_min_y, room_width, room_height):
                    if self._place_single_room(room_identifier, room_min_x, room_min_y, room_width, room_height):
                        placed = True
                        break
            if not placed:
                print(f"Warning: Could not place a pre-defined room at ({x},{y}).")

        # Then, place the remaining random rooms.
        for i in range(num_rooms):
            room_identifier = f"R{len(self.map.rooms) + 1}"
            placed = False
            for _ in range(self.placement_retries):
                room_width = random.randint(2, 5)
                room_height = random.randint(2, 5)
                room_min_x = random.randint(1, self.map.width - room_width + 1)
                room_min_y = random.randint(1, self.map.height - room_height + 1)
                
                if is_area_free(self.map, room_min_x, room_min_y, room_width, room_height):
                    if self._place_single_room(room_identifier, room_min_x, room_min_y, room_width, room_height):
                        placed = True
                        break
            if not placed:
                print(f"Warning: Could not place room R{i+1}.")
                
        print(f"Successfully scattered {len(self.map.rooms)} rooms.")

    def _punch_passages(self):
        """
        Randomly creates additional passages between adjacent areas to increase connectivity.
        This function iterates through all blocks and, based on a probability, may create
        a passage (door, secret door, etc.) where a wall exists between two different areas.
        """
        print("Punching optional passages for increased connectivity...")
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                block = self.map.get_block_at(x, y)
                if not block or block.empty:
                    continue
                
                # Check for walls to the north and east to avoid duplicate checks.
                for direction, (dx, dy) in {'north': (0, -1), 'east': (1, 0)}.items():
                    neighbor = self.map.get_block_at(x + dx, y + dy)
                    if neighbor and not neighbor.empty and block.area_uid != neighbor.area_uid:
                        # Check if there is a wall between the block and its neighbor.
                        if isinstance(getattr(block, direction, None), Wall):
                            if is_safe_to_punch_passage(self.map, block, direction):
                                if random.random() < PASSAGE_CREATION_CHANCE:
                                    # Determine the type of passage to create.
                                    is_door = random.random() < PASSAGE_PROB_DOOR
                                    is_secret = is_door and random.random() < PASSAGE_PROB_SECRET
                                    is_trapped = is_door and random.random() < PASSAGE_PROB_TRAPPED
                                    is_locked = is_door and random.random() < PASSAGE_PROB_LOCKED
                                    is_open = is_door and not is_locked and random.random() < PASSAGE_PROB_OPEN
                                    
                                    Passage.create(self.map, block, neighbor, direction, is_door, is_secret, is_trapped, is_locked, is_open)

    def _build_connectivity_graph(self):
        """
        Builds a graph representing the connectivity of all areas on the map.
        This graph is used to identify isolated or disconnected parts of the map.
        """
        print("Building connectivity graph...")
        self.map.connectivity.clear()
        for passage in self.map.passages:
            uid1 = passage.side1.area_uid
            uid2 = passage.side2.area_uid
            if uid1 and uid2 and uid1 != uid2:
                self.map.add_connection(uid1, uid2)

    def _ensure_map_connectivity(self):
        """
        Ensures that all areas on the map are interconnected.
        This function performs a breadth-first search (BFS) to find all reachable areas
        and then attempts to connect any isolated (unvisited) areas.
        """
        print("Ensuring map connectivity...")
        all_areas = self.map.rooms + self.map.hallways
        if not all_areas:
            return

        while True:
            self._build_connectivity_graph()
            
            # Start BFS from the first area.
            q = [all_areas[0].unique_id]
            visited_uids = {all_areas[0].unique_id}
            head = 0
            while head < len(q):
                current_uid = q[head]
                head += 1
                for neighbor_uid in self.map.connectivity.get(current_uid, []):
                    if neighbor_uid not in visited_uids:
                        visited_uids.add(neighbor_uid)
                        q.append(neighbor_uid)
            
            unvisited_uids = {area.unique_id for area in all_areas} - visited_uids
            if not unvisited_uids:
                print("Map is fully connected.")
                break

            print(f"Found {len(unvisited_uids)} unreachable areas. Attempting to connect...")
            connection_made = False
            for area_uid in unvisited_uids:
                unvisited_area = self.map.get_area_by_uid(area_uid)
                if not unvisited_area:
                    continue
                
                # Attempt to find a wall to break to connect to a visited area.
                for block in unvisited_area.blocks:
                    for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                        neighbor = self.map.get_block_at(block.location.x + dx, block.location.y + dy)
                        if neighbor and neighbor.area_uid in visited_uids and isinstance(getattr(block, direction), Wall):
                            print(f"Connecting {unvisited_area.identifier} to a visited area by creating a door.")
                            Passage.create(self.map, block, neighbor, direction, is_door=True)
                            connection_made = True
                            break
                    if connection_made:
                        break
                if connection_made:
                    break
            
            if not connection_made:
                print("Warning: Could not find a place to connect an isolated area. Map may be disconnected.")
                break

    def _renumber_and_validate(self):
        """
        Finalizes the map by renumbering all areas for a clean, sequential order
        and separating them into room and hallway lists for easy access.
        """
        print("Renumbering and validating map areas...")
        
        # Sort areas primarily by their vertical position, then horizontally.
        all_areas = sorted(self.map.rooms + self.map.hallways, 
                           key=lambda a: (get_center_of_blocks(a.blocks)[1], 
                                          get_center_of_blocks(a.blocks)[0]))
        
        # Rename and re-categorize areas.
        final_rooms = []
        final_hallways = []
        for i, area in enumerate(all_areas):
            new_identifier = f"Area {i + 1}"
            area.rename(new_identifier)
            if isinstance(area, Room):
                final_rooms.append(area)
            elif isinstance(area, Hallway):
                final_hallways.append(area)
        
        self.map.rooms = final_rooms
        self.map.hallways = final_hallways
        
        print("Validation and renumbering complete.")