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

    This class orchestrates the entire map generation process, including:
    - Placing rooms on an empty grid.
    - Connecting rooms with hallways using a minimum spanning tree and A* pathfinding.
    - Creating passages (doors, archways) between areas.
    - Ensuring the entire map is a single connected component.
    - Decorating rooms, hallways, and walls with content.
    - Renumbering and validating the final map structure.
    """
    def __init__(self, width=25, height=25, placement_retries=10, add_objects=None):
        """
        Initializes the map Generator.

        :param width: The width of the map grid.
        :param height: The height of the map grid.
        :param placement_retries: The number of times to attempt placing a room before giving up.
        :param add_objects: A list of specific objects to force into the map generation.
        """
        self.map = Map(width, height)
        self.placement_retries = placement_retries
        self.hallway_count = 0
        self.add_objects = add_objects if add_objects else []
        self.default_color = Color(0.8, 0.8, 0.8)  # Default color for rooms and hallways.

    def generate(self):
        """
        The main public method to generate and return a complete map.

        This method executes the sequence of steps required to create a valid,
        decorated, and fully connected dungeon map.

        :return: A fully generated Map object.
        """
        print("Starting map generation...")
        # 1. Initialize the grid with empty blocks.
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                self.map.blocks[(x, y)] = Block(location=Location(x, y), empty=True)
        
        # 2. Scatter a random number of rooms across the map.
        num_rooms = random.randint(self.map.MIN_ROOMS, self.map.MAX_ROOMS)
        print(f"Attempting to generate {num_rooms} rooms.")
        self._scatter_rooms(num_rooms)

        # 3. Connect rooms with hallways.
        self._connect_rooms_with_hallways()
        
        # 4. Punch additional random passages between adjacent areas.
        self._punch_passages()

        # 5. Ensure all rooms and hallways have the necessary passages.
        for room in self.map.rooms:
            self._ensure_room_passages(room)
        for hallway in self.map.hallways:
            self._ensure_hallway_passages(hallway)

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

    def _is_area_free(self, x, y, width, height):
        """
        Checks if a rectangular area on the map grid is free to be built upon.

        :param x: The starting x-coordinate of the area.
        :param y: The starting y-coordinate of the area.
        :param width: The width of the area.
        :param height: The height of the area.
        :return: True if the area is within bounds and consists entirely of empty blocks, False otherwise.
        """
        for i in range(y, y + height):
            for j in range(x, x + width):
                if not (1 <= j <= self.map.width and 1 <= i <= self.map.height):
                    return False  # Out of map bounds.
                block = self.map.get_block_at(j, i)
                if block is None or not block.empty:
                    return False  # Block is already occupied.
        return True

    def _place_single_room(self, room_identifier, room_min_x, room_min_y, room_width, room_height):
        """
        Creates and places a single room on the map at the specified location.

        This involves creating the Room object, updating the corresponding blocks on the grid,
        and setting the initial walls around the new room.

        :return: True if the room was placed successfully, False otherwise.
        """
        if room_width * room_height < 4: return False  # Room is too small.

        new_room = Room(identifier=room_identifier, color=self.default_color)
        
        blocks_for_room = []
        for y_offset in range(room_height):
            for x_offset in range(room_width):
                block = self.map.get_block_at(room_min_x + x_offset, room_min_y + y_offset)
                block.area_uid = new_room.unique_id
                block.empty = False
                blocks_for_room.append(block)
        
        new_room.blocks = blocks_for_room

        # After all blocks are assigned, set the walls.
        for block in blocks_for_room:
            block._set_initial_walls(self.map)
            
        self.map.add_room(new_room)
        return True

    def _scatter_rooms(self, num_rooms):
        """
        Randomly places a specified number of rooms on the map, avoiding overlaps.
        Also places rooms for any pre-defined objects with specific locations.
        """
        print("Scattering rooms...")
        
        # First, place rooms for objects that have a specific (x, y) coordinate.
        for obj_data in self.add_objects:
            obj_type, x, y = obj_data
            if x is None or y is None:
                continue

            room_identifier = f"R{num_rooms + 1}"
            
            placed = False
            for _ in range(self.placement_retries):
                room_width = random.randint(2, 5)
                room_height = random.randint(2, 5)
                # Try to place the room such that the specified (x, y) is within it.
                room_min_x = x - random.randint(1, room_width - 1)
                room_min_y = y - random.randint(1, room_height - 1)

                if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                    if self._place_single_room(room_identifier, room_min_x, room_min_y, room_width, room_height):
                        placed = True
                        num_rooms += 1
                        break
            if not placed:
                print(f"Warning: Could not place room for object at ({x},{y}).")

        # Then, place the rest of the rooms randomly.
        for i in range(num_rooms):
            room_identifier = f"R{i+1}"
            
            placed = False
            for _ in range(self.placement_retries):
                room_width = random.randint(2, 5)
                room_height = random.randint(2, 5)
                
                room_min_x = random.randint(1, self.map.width - room_width + 1)
                room_min_y = random.randint(1, self.map.height - room_height + 1)

                if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                    if self._place_single_room(room_identifier, room_min_x, room_min_y, room_width, room_height):
                        placed = True
                        break
            
            if not placed:
                print(f"Warning: Could not place room R{i+1}.")
        print(f"Successfully scattered {len(self.map.rooms)} rooms.")

    def _create_minimum_spanning_tree(self):
        """
        Builds a Minimum Spanning Tree (MST) of the rooms using Kruskal's algorithm.
        This ensures that all rooms are connected in the most efficient way possible,
        forming the primary structure for hallway connections.

        :return: A list of tuples, where each tuple contains two Room objects that should be connected.
        """
        if len(self.map.rooms) < 2: return []
        
        nodes = self.map.rooms
        edges = []
        # Create a fully connected graph of all rooms, with edge weights as the distance between them.
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                center1 = get_center_of_blocks(nodes[i].blocks)
                center2 = get_center_of_blocks(nodes[j].blocks)
                dist = self._heuristic(center1, center2)
                edges.append((dist, nodes[i], nodes[j]))
        
        edges.sort(key=lambda edge: edge[0])
        
        # Use a disjoint set data structure to build the MST.
        parent = {room.unique_id: room.unique_id for room in nodes}
        def find_set(room_uid):
            if parent[room_uid] == room_uid: return room_uid
            parent[room_uid] = find_set(parent[room_uid])
            return parent[room_uid]
        def unite_sets(uid1, uid2):
            uid1 = find_set(uid1)
            uid2 = find_set(uid2)
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
        Used as the heuristic for A* pathfinding.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _find_path_astar(self, start, end):
        """
        Finds a path between two points using the A* algorithm.
        The pathfinding prefers empty space and heavily penalizes paths that go through existing rooms.

        :param start: The starting (x, y) coordinate.
        :param end: The ending (x, y) coordinate.
        :return: A list of (x, y) tuples representing the path, or None if no path is found.
        """
        open_set = [(0, start)]
        came_from = {}
        g_score = { (x, y): float('inf') for x in range(self.map.width + 1) for y in range(self.map.height + 1) }
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
                if not (1 <= neighbor_loc[0] <= self.map.width and 1 <= neighbor_loc[1] <= self.map.height):
                    continue

                cost = 1
                block = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                # Penalize paths through existing rooms to encourage hallways in empty space.
                if block and not block.empty and neighbor_loc not in [start, end]:
                    cost = HALLWAY_OBSTACLE_COST

                tentative_g_score = g_score[current] + cost
                if tentative_g_score < g_score.get(neighbor_loc, float('inf')):
                    came_from[neighbor_loc] = current
                    g_score[neighbor_loc] = tentative_g_score
                    f_score[neighbor_loc] = tentative_g_score + self._heuristic(neighbor_loc, end)
                    heapq.heappush(open_set, (f_score[neighbor_loc], neighbor_loc))
        return None

    def _create_hallway_between_rooms(self, room1, room2):
        """
        Creates a hallway between two rooms by finding a path and converting the blocks along it.
        """
        start_block = random.choice(room1.blocks)
        end_block = random.choice(room2.blocks)
        
        path = self._find_path_astar((start_block.location.x, start_block.location.y), (end_block.location.x, end_block.location.y))
        
        if path and len(path) >= 4:
            self.hallway_count += 1
            hallway_id = f"H{self.hallway_count}"
            new_hallway = Hallway(identifier=hallway_id, connects_rooms=(room1.unique_id, room2.unique_id))
            
            blocks_for_hallway = []
            for loc in path:
                block = self.map.get_block_at(loc[0], loc[1])
                if block and block.empty:  # Only convert empty blocks to hallway parts.
                    block.area_uid = new_hallway.unique_id
                    block.empty = False
                    blocks_for_hallway.append(block)
            
            if blocks_for_hallway:
                new_hallway.blocks = blocks_for_hallway
                new_hallway.color = self.default_color
                self.map.add_hallway(new_hallway)

                for block in blocks_for_hallway:
                    block._set_initial_walls(self.map)

    def _connect_rooms_with_hallways(self):
        """
        Connects all rooms with hallways based on the Minimum Spanning Tree.
        """
        print("Connecting rooms with hallways...")
        if len(self.map.rooms) < 2: return

        connections = self._create_minimum_spanning_tree()
        print(f"MST determined {len(connections)} connections to be made.")

        for room1, room2 in connections:
            self._create_hallway_between_rooms(room1, room2)

    def _create_passage_between_blocks(self, block1, block2, direction, is_door, is_secret=False, is_trapped=False, is_locked=False, is_open=False):
        """
        Creates a Passage object between two adjacent blocks, replacing the wall.
        """
        description = None
        if is_trapped:
            description = random.choice(TRAPPED_DOOR_DESCRIPTIONS)

        passage = Passage(side1=block1, side2=block2, is_door=is_door, is_secret=is_secret, is_trapped=is_trapped, is_locked=is_locked, is_open=is_open, description=description)
        setattr(block1, direction, passage)
        opposite_direction = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction]
        setattr(block2, opposite_direction, passage)
        self.map.add_passage(passage)
        return True

    def _punch_passages(self):
        """
        Iterates through the map and randomly creates additional passages (doors or openings)
        between adjacent but disconnected areas to create more loops and interesting layouts.
        """
        print("Punching optional passages...")
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                block = self.map.get_block_at(x, y)
                if not block.empty:
                    # Check north and east to avoid double-checking each boundary.
                    for direction, (dx, dy) in {'north': (0, -1), 'east': (1, 0)}.items():
                        neighbor = self.map.get_block_at(x + dx, y + dy)
                        if neighbor and not neighbor.empty and block.area_uid != neighbor.area_uid:
                            # If there's a wall between two different areas, consider making a passage.
                            if isinstance(getattr(block, direction), Wall):
                                if random.random() < PASSAGE_CREATION_CHANCE:
                                    is_door = random.random() < PASSAGE_PROB_DOOR
                                    is_secret = random.random() < PASSAGE_PROB_SECRET
                                    is_trapped = False
                                    is_locked = False
                                    is_open = False
                                    if is_door:
                                        is_trapped = random.random() < PASSAGE_PROB_TRAPPED
                                        is_locked = random.random() < PASSAGE_PROB_LOCKED
                                        if not is_locked:
                                            is_open = random.random() < PASSAGE_PROB_OPEN
                                    self._create_passage_between_blocks(block, neighbor, direction, is_door, is_secret, is_trapped, is_locked, is_open)

    def _create_passage_between_hallway_and_room(self, hallway, room_uid):
        """
        Finds the best candidate location for a passage between a hallway and a room and creates it.
        Prefers creating passages where a solid wall already exists.
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
                    elif not best_candidate: # Fallback to a non-wall connection if needed.
                        best_candidate = (h_block, neighbor, direction)
            if best_candidate and isinstance(getattr(best_candidate[0], best_candidate[2]), Wall):
                break

        if best_candidate:
            h_block, neighbor, direction = best_candidate
            self._create_passage_between_blocks(h_block, neighbor, direction, is_door=True)
            return True

        return False

    def _create_passage_between_adjacent_rooms(self, room1, room2):
        """
        Creates a passage at the first available wall segment between two adjacent rooms.
        """
        for r1_block in room1.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor_loc = (r1_block.location.x + dx, r1_block.location.y + dy)
                neighbor = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                if neighbor and neighbor.area_uid == room2.unique_id and isinstance(getattr(r1_block, direction), Wall):
                    self._create_passage_between_blocks(r1_block, neighbor, direction, is_door=True)
                    return True
        return False

    def _ensure_room_passages(self, room):
        """
        Ensures a room has at least one passage connecting it to another area.
        If a room is isolated, this method will force a connection.
        """
        if room.count_passages(self.map) < 1:
            print(f"Room {room.identifier} has no passages. Adding one.")
            for r_block in room.blocks:
                for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                    neighbor = self.map.get_block_at(r_block.location.x + dx, r_block.location.y + dy)
                    if neighbor and not neighbor.empty and neighbor.area_uid != room.unique_id:
                        neighbor_area = self.map.get_area_by_uid(neighbor.area_uid)
                        if isinstance(neighbor_area, Room):
                            if self._create_passage_between_adjacent_rooms(room, neighbor_area):
                                return

    def _ensure_hallway_passages(self, hallway):
        """
        Ensures a hallway has passages connecting to its designated start and end rooms.
        """
        if hallway.count_passages(self.map) < 2:
            print(f"Hallway {hallway.identifier} is missing passages. Attempting to add them.")
            for room_uid in hallway.connects_rooms:
                self._create_passage_between_hallway_and_room(hallway, room_uid)

    def _build_connectivity_graph(self):
        """
        Builds the `map.connectivity` graph based on the current list of passages.
        This graph represents which areas are directly connected to each other.
        """
        print("Building connectivity graph...")
        self.map.connectivity = {}
        for passage in self.map.passages:
            uid1 = passage.side1.area_uid
            uid2 = passage.side2.area_uid
            if uid1 and uid2:
                self.map.add_connection(uid1, uid2)

    def _ensure_map_connectivity(self):
        """
        Ensures all areas on the map are part of a single connected component.
        It uses a Breadth-First Search (BFS) to find all reachable areas from a starting point.
        If any areas are unreachable, it attempts to create new passages to connect them.
        """
        print("Ensuring map connectivity...")
        all_areas = self.map.rooms + self.map.hallways
        if not all_areas:
            return

        while True:
            self._build_connectivity_graph()
            
            # Perform a BFS to find all reachable areas.
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

            all_area_uids = {area.unique_id for area in all_areas}
            unvisited_uids = all_area_uids - visited_uids

            if not unvisited_uids:
                print("Map is fully connected.")
                break  # All areas are connected.

            print(f"Found {len(unvisited_uids)} unreachable areas. Attempting to connect...")
            
            # Attempt to connect one of the unvisited areas.
            connection_made = False
            for area_uid in unvisited_uids:
                unvisited_area = self.map.get_area_by_uid(area_uid)
                if not unvisited_area: continue

                # Search for a wall adjacent to a visited area.
                for block in unvisited_area.blocks:
                    for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                        neighbor = self.map.get_block_at(block.location.x + dx, block.location.y + dy)
                        if neighbor and neighbor.area_uid in visited_uids:
                            if isinstance(getattr(block, direction), Wall):
                                print(f"Connecting {unvisited_area.identifier} to visited area by creating a door.")
                                self._create_passage_between_blocks(block, neighbor, direction, is_door=True)
                                connection_made = True
                                break
                    if connection_made:
                        break
                if connection_made:
                    break
            
            if not connection_made:
                print("Warning: Could not find a place to connect an isolated area. Aborting connectivity check.")
                break

    def _decorate_rooms(self):
        """
        Decorates all rooms on the map with items, objects, and encounters.
        Handles both randomly placed content and user-specified forced objects.
        """
        print("Decorating rooms...")
        
        forced_objects_with_loc = [obj for obj in self.add_objects if obj[1] is not None and obj[2] is not None]
        forced_objects_no_loc = [obj for obj in self.add_objects if obj[1] is None and obj[2] is None]

        rooms_with_forced_objects = set()

        # Place objects with specific locations first.
        for obj_type, x, y in forced_objects_with_loc:
            area = self.map.get_area_by_location(x, y)
            if area and isinstance(area, Room):
                area.decorate(self.map, forced_object=(obj_type, (x, y)))
                rooms_with_forced_objects.add(area.unique_id)

        # Place objects without specific locations in random available rooms.
        available_rooms = [room for room in self.map.rooms if room.unique_id not in rooms_with_forced_objects]
        random.shuffle(available_rooms)

        for obj_type, _, _ in forced_objects_no_loc:
            if available_rooms:
                room = available_rooms.pop()
                room.decorate(self.map, forced_object=(obj_type, None))
                rooms_with_forced_objects.add(room.unique_id)
            else:
                print(f"Warning: No available rooms to place object of type {obj_type}.")

        # Decorate the remaining rooms randomly.
        for room in self.map.rooms:
            if room.unique_id not in rooms_with_forced_objects:
                room.decorate(self.map)

    def _decorate_hallways(self):
        """
        Decorates all hallways on the map with items and encounters.
        """
        print("Decorating hallways...")
        for hallway in self.map.hallways:
            hallway.decorate(self.map)

    def _decorate_walls(self):
        """
        Adds descriptive decorations to random wall segments throughout the map.
        """
        print("Decorating walls...")
        all_walls = set()
        # Collect all wall segments.
        for block in self.map.blocks.values():
            for direction in ['north', 'south', 'east', 'west']:
                if isinstance(getattr(block, direction), Wall):
                    all_walls.add((block, direction))
        
        processed_blocks = set()
        for block, direction in all_walls:
            if block.unique_id in processed_blocks:
                continue

            # Find continuous segments of walls.
            segment = [block.location]
            
            # This logic for finding segments is complex and could be simplified.
            # It attempts to trace along a wall line to find its full extent.
            if direction in ['north', 'south']:
                curr_loc = (block.location.x, block.location.y - 1)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1])
                    segment.append(b.location)
                    processed_blocks.add(b.unique_id)
                    curr_loc = (curr_loc[0], curr_loc[1] - 1)
                curr_loc = (block.location.x, block.location.y + 1)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1])
                    segment.append(b.location)
                    processed_blocks.add(b.unique_id)
                    curr_loc = (curr_loc[0], curr_loc[1] + 1)
            else: # 'east', 'west'
                curr_loc = (block.location.x - 1, block.location.y)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1])
                    segment.append(b.location)
                    processed_blocks.add(b.unique_id)
                    curr_loc = (curr_loc[0] - 1, curr_loc[1])
                curr_loc = (block.location.x + 1, block.location.y)
                while self.map.get_block_at(curr_loc[0], curr_loc[1]) and (self.map.get_block_at(curr_loc[0], curr_loc[1]), direction) in all_walls:
                    b = self.map.get_block_at(curr_loc[0], curr_loc[1])
                    segment.append(b.location)
                    processed_blocks.add(b.unique_id)
                    curr_loc = (curr_loc[0] + 1, curr_loc[1])

            # Randomly decide whether to add a decoration to this wall segment.
            if random.random() < WALL_DECORATION_CHANCE:
                desc = random.choice(WALL_DECORATIONS)
                decoration = WallDecoration(locations=segment, direction=direction, description=desc, area_uid=block.area_uid)
                self.map.add_wall_decoration(decoration)

    def _renumber_and_validate(self):
        """
        Finalizes the map by renumbering all areas for a geographically logical order.
        This makes the map index easier for a human to read.
        """
        print("Renumbering and validating map...")
        
        # Sort areas from top to bottom, then right to left.
        all_areas = sorted(self.map.rooms + self.map.hallways, key=lambda a: (get_center_of_blocks(a.blocks)[1], -get_center_of_blocks(a.blocks)[0]), reverse=True)
        
        for i, area in enumerate(all_areas):
            area.rename(f"Area {i+1}")

        # Re-populate the map's room and hallway lists with the sorted and renumbered areas.
        self.map.rooms = [area for area in all_areas if isinstance(area, Room)]
        self.map.hallways = [area for area in all_areas if isinstance(area, Hallway)]

        print("Validation complete.")
