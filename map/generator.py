"""
This module contains the main Generator class, which is responsible for orchestrating
the entire procedural generation of the dungeon map.
"""
import random
import math
import heapq
from reportlab.lib.colors import Color

from .map import Map
from .room import Room
from .hallway import Hallway
from .block import Block
from .location import Location
from .wall import Wall
from .passage import Passage
from .wall_decoration import WallDecoration
from .utils import get_center_of_blocks
from .constants import WALL_DECORATION_CHANCE, HALLWAY_OBSTACLE_COST, PASSAGE_CREATION_CHANCE, \
    PASSAGE_PROB_DOOR, PASSAGE_PROB_SECRET, PASSAGE_PROB_TRAPPED, PASSAGE_PROB_LOCKED, PASSAGE_PROB_OPEN
from .text import WALL_DECORATIONS, TRAPPED_DOOR_DESCRIPTIONS


class Generator:
    """
    The main class for generating the dungeon map.

    This class can generate maps using two different algorithms:
    1.  **Hallway-based**: Connects rooms with hallways using A* pathfinding.
    2.  **Maze-based**: Carves a maze in the empty space and connects rooms to it.
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
        self.default_color = Color(0.8, 0.8, 0.8)  # Default color for rooms and hallways.
        self.maze_mode = maze_mode

    def generate(self):
        """
        The main public method to generate and return a complete map.

        This method executes the sequence of steps required to create a valid,
        decorated, and fully connected dungeon map, based on the selected mode.

        :return: A fully generated Map object.
        """
        print(f"Starting map generation... (Mode: {'Maze' if self.maze_mode else 'Hallway'})")
        # 1. Initialize the grid with empty blocks.
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                self.map.blocks[(x, y)] = Block(location=Location(x, y), empty=True)
        
        # 2. Scatter a random number of rooms across the map.
        num_rooms = random.randint(self.map.MIN_ROOMS, self.map.MAX_ROOMS)
        print(f"Attempting to generate {num_rooms} rooms.")
        self._scatter_rooms(num_rooms)

        if self.maze_mode:
            # 3a. Carve a maze out of the remaining empty space.
            self._carve_maze()
            # 4a. Connect rooms to the maze.
            self._connect_rooms_to_maze()
        else:
            # 3b. Connect rooms with hallways.
            self._connect_rooms_with_hallways()
            # 4b. Ensure all rooms and hallways have the necessary passages.
            for room in self.map.rooms:
                self._ensure_room_passages(room)
            for hallway in self.map.hallways:
                self._ensure_hallway_passages(hallway)

        # 5. Punch additional random passages between adjacent areas.
        self._punch_passages()

        # 6. Verify and enforce full map connectivity.
        self._ensure_map_connectivity()

        # 7. Decorate the map with content.
        self._decorate_rooms()
        self._decorate_hallways()
        self._decorate_walls()
        
        # 8. Finalize the map by renumbering areas for a logical layout.
        self._renumber_and_validate()
        
        print(f"Map generation complete with {len(self.map.rooms) + len(self.map.hallways)} areas.")
        return self.map

    def _carve_maze(self):
        """
        Carves a maze into all empty blocks of the map using a recursive backtracking algorithm.
        This robust version iterates through the grid on a 2x2 step to ensure all isolated pockets
        of empty space are filled with a proper maze structure with walls.
        (Used only in maze_mode)
        """
        print("Carving maze...")
        
        # A single hallway object will represent the entire maze.
        self.hallway_count += 1
        maze_hallway = Hallway(identifier=f"H{self.hallway_count}")
        self.map.add_hallway(maze_hallway)

        # Iterate through every potential path cell on a 2x2 grid (i.e., odd coordinates).
        # This ensures that we leave a 1-block space for walls between the paths.
        for y in range(1, self.map.height + 1, 2):
            for x in range(1, self.map.width + 1, 2):
                start_block = self.map.get_block_at(x, y)
                
                # If we find an empty block, it means this part of the map is uncarved.
                # Start a new carving session from this point.
                if start_block and start_block.empty:
                    
                    stack = [(x, y)]
                    
                    while stack:
                        cx, cy = stack[-1]
                        current_block = self.map.get_block_at(cx, cy)

                        # Mark the current block as part of the maze.
                        if current_block and current_block.empty:
                            current_block.area_uid = maze_hallway.unique_id
                            current_block.empty = False
                            maze_hallway.blocks.append(current_block)

                        # Get potential neighbors, jumping 2 blocks at a time.
                        neighbors = []
                        for dx, dy in [(0, -2), (0, 2), (2, 0), (-2, 0)]:
                            nx, ny = cx + dx, cy + dy
                            
                            if 1 <= nx <= self.map.width and 1 <= ny <= self.map.height:
                                neighbor_block = self.map.get_block_at(nx, ny)
                                # A neighbor is valid if it's within an empty region.
                                if neighbor_block and neighbor_block.empty:
                                    neighbors.append((nx, ny, (cx + dx // 2, cy + dy // 2)))

                        if neighbors:
                            nx, ny, (px, py) = random.choice(neighbors)
                            
                            # Carve the wall between the current cell and the neighbor.
                            path_block = self.map.get_block_at(px, py)
                            if path_block and path_block.empty:
                                path_block.area_uid = maze_hallway.unique_id
                                path_block.empty = False
                                maze_hallway.blocks.append(path_block)
                            
                            # Move to the neighbor.
                            stack.append((nx, ny))
                        else:
                            # Backtrack if there are no valid neighbors.
                            stack.pop()

        # After all pockets are carved, set the walls for the entire maze area.
        for block in maze_hallway.blocks:
            block._set_initial_walls(self.map)
        print("Maze carving complete.")

    def _connect_rooms_to_maze(self):
        """
        Ensures every room has at least one passage connecting it to the maze.
        (Used only in maze_mode)
        """
        print("Connecting rooms to maze...")
        if not self.map.hallways:
            print("Warning: No maze (hallway) found to connect rooms to.")
            return
            
        maze_uid = self.map.hallways[0].unique_id

        for room in self.map.rooms:
            potential_doors = []
            for r_block in room.blocks:
                for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                    neighbor = self.map.get_block_at(r_block.location.x + dx, r_block.location.y + dy)
                    if neighbor and neighbor.area_uid == maze_uid and isinstance(getattr(r_block, direction), Wall):
                        potential_doors.append((r_block, neighbor, direction))
            
            if potential_doors:
                door_block1, door_block2, door_direction = random.choice(potential_doors)
                self._create_passage_between_blocks(door_block1, door_block2, door_direction, is_door=True)
            else:
                print(f"Warning: Could not find a suitable wall to connect Room {room.identifier} to the maze.")

    def _is_area_free(self, x, y, width, height):
        """
        Checks if a rectangular area on the map grid is free to be built upon.
        """
        for i in range(y, y + height):
            for j in range(x, x + width):
                if not (1 <= j <= self.map.width and 1 <= i <= self.map.height):
                    return False
                block = self.map.get_block_at(j, i)
                if block is None or not block.empty:
                    return False
        return True

    def _place_single_room(self, room_identifier, room_min_x, room_min_y, room_width, room_height):
        """
        Creates and places a single room on the map.
        """
        if room_width * room_height < 4: return False

        new_room = Room(identifier=room_identifier, color=self.default_color)
        
        blocks_for_room = []
        for y_offset in range(room_height):
            for x_offset in range(room_width):
                block = self.map.get_block_at(room_min_x + x_offset, room_min_y + y_offset)
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
        Randomly places a specified number of rooms on the map.
        """
        print("Scattering rooms...")
        
        for obj_data in self.add_objects:
            obj_type, x, y = obj_data
            if x is None or y is None: continue
            room_identifier = f"R{num_rooms + 1}"
            placed = False
            for _ in range(self.placement_retries):
                room_width, room_height = random.randint(2, 5), random.randint(2, 5)
                room_min_x, room_min_y = x - random.randint(1, room_width - 1), y - random.randint(1, room_height - 1)
                if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                    if self._place_single_room(room_identifier, room_min_x, room_min_y, room_width, room_height):
                        placed = True
                        num_rooms += 1
                        break
            if not placed: print(f"Warning: Could not place room for object at ({x},{y}).")

        for i in range(num_rooms):
            room_identifier = f"R{i+1}"
            placed = False
            for _ in range(self.placement_retries):
                room_width, room_height = random.randint(2, 5), random.randint(2, 5)
                room_min_x, room_min_y = random.randint(1, self.map.width - room_width + 1), random.randint(1, self.map.height - room_height + 1)
                if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                    if self._place_single_room(room_identifier, room_min_x, room_min_y, room_width, room_height):
                        placed = True
                        break
            if not placed: print(f"Warning: Could not place room R{i+1}.")
        print(f"Successfully scattered {len(self.map.rooms)} rooms.")

    def _create_minimum_spanning_tree(self):
        """
        Builds a Minimum Spanning Tree (MST) of the rooms using Kruskal's algorithm.
        (Used only in hallway mode)
        """
        if len(self.map.rooms) < 2: return []
        
        nodes = self.map.rooms
        edges = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                center1, center2 = get_center_of_blocks(nodes[i].blocks), get_center_of_blocks(nodes[j].blocks)
                dist = self._heuristic(center1, center2)
                edges.append((dist, nodes[i], nodes[j]))
        
        edges.sort(key=lambda edge: edge[0])
        
        parent = {room.unique_id: room.unique_id for room in nodes}
        def find_set(room_uid):
            if parent[room_uid] == room_uid: return room_uid
            parent[room_uid] = find_set(parent[room_uid])
            return parent[room_uid]
        def unite_sets(uid1, uid2):
            uid1, uid2 = find_set(uid1), find_set(uid2)
            if uid1 != uid2: parent[uid2] = uid1

        mst_connections = []
        for dist, room1, room2 in edges:
            if find_set(room1.unique_id) != find_set(room2.unique_id):
                unite_sets(room1.unique_id, room2.unique_id)
                mst_connections.append((room1, room2))
        return mst_connections

    def _heuristic(self, a, b):
        """
        Calculates the Manhattan distance between two points (a, b).
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _find_path_astar(self, start, end):
        """
        Finds a path between two points using the A* algorithm.
        (Used only in hallway mode)
        """
        open_set = [(0, start)]
        came_from, g_score = {}, { (x, y): float('inf') for x in range(self.map.width + 1) for y in range(self.map.height + 1) }
        g_score[start] = 0
        f_score = { (x, y): float('inf') for x in range(self.map.width + 1) for y in range(self.map.height + 1) }
        f_score[start] = self._heuristic(start, end)

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_loc = (current[0] + dx, current[1] + dy)
                if not (1 <= neighbor_loc[0] <= self.map.width and 1 <= neighbor_loc[1] <= self.map.height): continue

                cost = 1
                block = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                if block and not block.empty and neighbor_loc not in [start, end]: cost = HALLWAY_OBSTACLE_COST

                tentative_g_score = g_score[current] + cost
                if tentative_g_score < g_score.get(neighbor_loc, float('inf')):
                    came_from[neighbor_loc], g_score[neighbor_loc] = current, tentative_g_score
                    f_score[neighbor_loc] = tentative_g_score + self._heuristic(neighbor_loc, end)
                    heapq.heappush(open_set, (f_score[neighbor_loc], neighbor_loc))
        return None

    def _create_hallway_between_rooms(self, room1, room2):
        """
        Creates a hallway between two rooms.
        (Used only in hallway mode)
        """
        start_block, end_block = random.choice(room1.blocks), random.choice(room2.blocks)
        path = self._find_path_astar((start_block.location.x, start_block.location.y), (end_block.location.x, end_block.location.y))
        
        if path and len(path) >= 4:
            self.hallway_count += 1
            new_hallway = Hallway(identifier=f"H{self.hallway_count}", connects_rooms=(room1.unique_id, room2.unique_id))
            
            blocks_for_hallway = []
            for loc in path:
                block = self.map.get_block_at(loc[0], loc[1])
                if block and block.empty:
                    block.area_uid, block.empty = new_hallway.unique_id, False
                    blocks_for_hallway.append(block)
            
            if blocks_for_hallway:
                new_hallway.blocks, new_hallway.color = blocks_for_hallway, self.default_color
                self.map.add_hallway(new_hallway)
                for block in blocks_for_hallway: block._set_initial_walls(self.map)

    def _connect_rooms_with_hallways(self):
        """
        Connects all rooms with hallways based on the MST.
        (Used only in hallway mode)
        """
        print("Connecting rooms with hallways...")
        if len(self.map.rooms) < 2: return

        connections = self._create_minimum_spanning_tree()
        print(f"MST determined {len(connections)} connections to be made.")
        for room1, room2 in connections: self._create_hallway_between_rooms(room1, room2)

    def _create_passage_between_blocks(self, block1, block2, direction, is_door, is_secret=False, is_trapped=False, is_locked=False, is_open=False):
        """
        Creates a Passage object between two adjacent blocks, ensuring no duplicates.
        This method first removes any existing passage at the same location before creating a new one.
        """
        opposite_direction = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction]

        # Clean up any existing passage at this boundary to prevent duplicates.
        existing_passage = getattr(block1, direction)
        if isinstance(existing_passage, Passage):
            if existing_passage in self.map.passages:
                self.map.passages.remove(existing_passage)

        # Create the new passage.
        description = random.choice(TRAPPED_DOOR_DESCRIPTIONS) if is_trapped else None
        passage = Passage(side1=block1, side2=block2, is_door=is_door, is_secret=is_secret, is_trapped=is_trapped, is_locked=is_locked, is_open=is_open, description=description)
        
        # Set the new passage on both blocks.
        setattr(block1, direction, passage)
        setattr(block2, opposite_direction, passage)
        
        # Add the new passage to the map's central list.
        self.map.add_passage(passage)
        return True

    def _is_safe_to_punch_passage(self, block, direction):
        """
        Checks if it's safe to create a passage in a given direction from a block.
        It is considered unsafe if the adjacent wall segments are already passages.
        This prevents passages from being placed next to each other.

        :param block: The block from which the passage is proposed.
        :param direction: The direction of the proposed passage ('north', 'south', 'east', 'west').
        :return: True if it is safe to place a passage, False otherwise.
        """
        x, y = block.location.x, block.location.y

        # Define the checks based on the direction of the wall.
        if direction in ['north', 'south']:
            # For a horizontal wall, check the walls to the east and west.
            check_coords = [(x - 1, y), (x + 1, y)]
        elif direction in ['east', 'west']:
            # For a vertical wall, check the walls to the north and south.
            check_coords = [(x, y - 1), (x, y + 1)]
        else:
            return True # Should not happen

        for cx, cy in check_coords:
            adj_block = self.map.get_block_at(cx, cy)
            if adj_block:
                # Check if the corresponding wall on the adjacent block is a passage.
                if isinstance(getattr(adj_block, direction, None), Passage):
                    return False
        
        return True

    def _punch_passages(self):
        """
        Randomly creates additional passages between adjacent but disconnected areas,
        ensuring that passages are not placed next to each other.
        """
        print("Punching optional passages...")
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                block = self.map.get_block_at(x, y)
                if not block or block.empty:
                    continue
                
                # Check north and east to avoid double-checking each boundary.
                for direction, (dx, dy) in {'north': (0, -1), 'east': (1, 0)}.items():
                    neighbor = self.map.get_block_at(x + dx, y + dy)
                    
                    # Ensure there's a wall between two different, non-empty areas.
                    if neighbor and not neighbor.empty and block.area_uid != neighbor.area_uid and isinstance(getattr(block, direction), Wall):
                        
                        # Check if it's safe to place a passage here.
                        if self._is_safe_to_punch_passage(block, direction):
                            if random.random() < PASSAGE_CREATION_CHANCE:
                                is_door = random.random() < PASSAGE_PROB_DOOR
                                is_secret, is_trapped, is_locked, is_open = False, False, False, False
                                if is_door:
                                    is_secret = random.random() < PASSAGE_PROB_SECRET
                                    is_trapped = random.random() < PASSAGE_PROB_TRAPPED
                                    is_locked = random.random() < PASSAGE_PROB_LOCKED
                                    if not is_locked: is_open = random.random() < PASSAGE_PROB_OPEN
                                self._create_passage_between_blocks(block, neighbor, direction, is_door, is_secret, is_trapped, is_locked, is_open)

    def _create_passage_between_hallway_and_room(self, hallway, room_uid):
        """
        Creates a passage between a hallway and a room.
        (Used only in hallway mode)
        """
        best_candidate = None
        for h_block in hallway.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor = self.map.get_block_at(h_block.location.x + dx, h_block.location.y + dy)
                if neighbor and neighbor.area_uid == room_uid:
                    connection = getattr(h_block, direction)
                    if isinstance(connection, Wall):
                        best_candidate = (h_block, neighbor, direction)
                        break
                    elif not best_candidate: best_candidate = (h_block, neighbor, direction)
            if best_candidate and isinstance(getattr(best_candidate[0], best_candidate[2]), Wall): break
        if best_candidate:
            h_block, neighbor, direction = best_candidate
            self._create_passage_between_blocks(h_block, neighbor, direction, is_door=True)
            return True
        return False

    def _create_passage_between_adjacent_rooms(self, room1, room2):
        """
        Creates a passage between two adjacent rooms.
        (Used only in hallway mode)
        """
        for r1_block in room1.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor = self.map.get_block_at(r1_block.location.x + dx, r1_block.location.y + dy)
                if neighbor and neighbor.area_uid == room2.unique_id and isinstance(getattr(r1_block, direction), Wall):
                    self._create_passage_between_blocks(r1_block, neighbor, direction, is_door=True)
                    return True
        return False

    def _ensure_room_passages(self, room):
        """
        Ensures a room has at least one passage.
        (Used only in hallway mode)
        """
        if room.count_passages(self.map) < 1:
            print(f"Room {room.identifier} has no passages. Adding one.")
            for r_block in room.blocks:
                for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                    neighbor = self.map.get_block_at(r_block.location.x + dx, r_block.location.y + dy)
                    if neighbor and not neighbor.empty and neighbor.area_uid != room.unique_id:
                        neighbor_area = self.map.get_area_by_uid(neighbor.area_uid)
                        if isinstance(neighbor_area, Room):
                            if self._create_passage_between_adjacent_rooms(room, neighbor_area): return

    def _ensure_hallway_passages(self, hallway):
        """
        Ensures a hallway connects to its designated rooms.
        (Used only in hallway mode)
        """
        if hallway.count_passages(self.map) < 2:
            print(f"Hallway {hallway.identifier} is missing passages. Attempting to add them.")
            for room_uid in hallway.connects_rooms: self._create_passage_between_hallway_and_room(hallway, room_uid)

    def _build_connectivity_graph(self):
        """
        Builds the connectivity graph for the map.
        """
        print("Building connectivity graph...")
        self.map.connectivity = {}
        for passage in self.map.passages:
            uid1, uid2 = passage.side1.area_uid, passage.side2.area_uid
            if uid1 and uid2: self.map.add_connection(uid1, uid2)

    def _ensure_map_connectivity(self):
        """
        Ensures all areas on the map are part of a single connected component.
        """
        print("Ensuring map connectivity...")
        all_areas = self.map.rooms + self.map.hallways
        if not all_areas: return

        while True:
            self._build_connectivity_graph()
            q, visited_uids = [all_areas[0].unique_id], {all_areas[0].unique_id}
            head = 0
            while head < len(q):
                current_uid = q[head]; head += 1
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
                if not unvisited_area: continue
                for block in unvisited_area.blocks:
                    for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                        neighbor = self.map.get_block_at(block.location.x + dx, block.location.y + dy)
                        if neighbor and neighbor.area_uid in visited_uids and isinstance(getattr(block, direction), Wall):
                            print(f"Connecting {unvisited_area.identifier} to visited area by creating a door.")
                            self._create_passage_between_blocks(block, neighbor, direction, is_door=True)
                            connection_made = True
                            break
                    if connection_made: break
                if connection_made: break
            if not connection_made:
                print("Warning: Could not find a place to connect an isolated area. Aborting connectivity check.")
                break

    def _decorate_rooms(self):
        """
        Decorates all rooms on the map.
        """
        print("Decorating rooms...")
        forced_objects_with_loc = [obj for obj in self.add_objects if obj[1] is not None and obj[2] is not None]
        forced_objects_no_loc = [obj for obj in self.add_objects if obj[1] is None and obj[2] is None]
        rooms_with_forced_objects = set()

        for obj_type, x, y in forced_objects_with_loc:
            area = self.map.get_area_by_location(x, y)
            if area and isinstance(area, Room):
                area.decorate(self.map, forced_object=(obj_type, (x, y)))
                rooms_with_forced_objects.add(area.unique_id)

        available_rooms = [room for room in self.map.rooms if room.unique_id not in rooms_with_forced_objects]
        random.shuffle(available_rooms)

        for obj_type, _, _ in forced_objects_no_loc:
            if available_rooms:
                room = available_rooms.pop()
                room.decorate(self.map, forced_object=(obj_type, None))
                rooms_with_forced_objects.add(room.unique_id)
            else: print(f"Warning: No available rooms to place object of type {obj_type}.")

        for room in self.map.rooms:
            if room.unique_id not in rooms_with_forced_objects: room.decorate(self.map)

    def _decorate_hallways(self):
        """
        Decorates all hallways on the map.
        """
        print("Decorating hallways...")
        for hallway in self.map.hallways: hallway.decorate(self.map)

    def _decorate_walls(self):
        """
        Adds descriptive decorations to random wall segments.
        """
        print("Decorating walls...")
        all_walls = set()
        for block in self.map.blocks.values():
            for direction in ['north', 'south', 'east', 'west']:
                if isinstance(getattr(block, direction), Wall): all_walls.add((block, direction))
        
        processed_blocks = set()
        for block, direction in all_walls:
            if block.unique_id in processed_blocks: continue
            segment = [block.location]
            # This logic for finding segments is complex and could be simplified.
            if direction in ['north', 'south']:
                curr_loc = (block.location.x, block.location.y - 1)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1]); segment.append(b.location); processed_blocks.add(b.unique_id); curr_loc = (curr_loc[0], curr_loc[1] - 1)
                curr_loc = (block.location.x, block.location.y + 1)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1]); segment.append(b.location); processed_blocks.add(b.unique_id); curr_loc = (curr_loc[0], curr_loc[1] + 1)
            else: # 'east', 'west'
                curr_loc = (block.location.x - 1, block.location.y)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1]); segment.append(b.location); processed_blocks.add(b.unique_id); curr_loc = (curr_loc[0] - 1, curr_loc[1])
                curr_loc = (block.location.x + 1, block.location.y)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1]); segment.append(b.location); processed_blocks.add(b.unique_id); curr_loc = (curr_loc[0] + 1, curr_loc[1])

            if random.random() < WALL_DECORATION_CHANCE:
                desc = random.choice(WALL_DECORATIONS)
                decoration = WallDecoration(locations=segment, direction=direction, description=desc, area_uid=block.area_uid)
                self.map.add_wall_decoration(decoration)

    def _renumber_and_validate(self):
        """
        Finalizes the map by renumbering all areas for a logical order.
        """
        print("Renumbering and validating map...")
        all_areas = sorted(self.map.rooms + self.map.hallways, key=lambda a: (get_center_of_blocks(a.blocks)[1], -get_center_of_blocks(a.blocks)[0]), reverse=True)
        for i, area in enumerate(all_areas): area.rename(f"Area {i+1}")
        self.map.rooms = [area for area in all_areas if isinstance(area, Room)]
        self.map.hallways = [area for area in all_areas if isinstance(area, Hallway)]
        print("Validation complete.")