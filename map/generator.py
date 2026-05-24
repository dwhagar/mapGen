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
from .constants import WALL_DECORATION_CHANCE, PASSAGE_IS_DOOR
from .text import WALL_DECORATIONS

class Generator:
    """
    The main class for generating the map.
    """
    def __init__(self, width=25, height=25, placement_retries=10, add_object=None):
        """
        Initializes the Generator.

        :param placement_retries: The number of times to retry placing a room.
        :param add_object: An object to add to the map.
        """
        self.map = Map(width, height)
        self.placement_retries = placement_retries
        self.hallway_count = 0
        self.add_object = add_object

    def generate(self):
        """
        Generates the map.
        """
        print("Starting map generation...")
        # 1. Fill the map with empty blocks
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                self.map.blocks[(x, y)] = Block(location=Location(x, y), empty=True)
        
        # 2. Determine the number, size, etc of all the rooms.
        num_rooms = random.randint(self.map.MIN_ROOMS, self.map.MAX_ROOMS)
        print(f"Attempting to generate {num_rooms} rooms.")
        self._scatter_rooms(num_rooms)

        # 4. Add hallways to connect the rooms together.
        self._connect_rooms_with_hallways()

        # Walk all blocks and create walls
        for block in self.map.blocks.values():
            block.create_walls(self.map)

        # 7. Add passages
        self._punch_passages()

        # 9. Go through each room, make sure each room has at least 1 passage to that space.
        for room in self.map.rooms:
            if room.count_passages(self.map) < 1:
                print(f"Room {room.identifier} has no passages. Adding one.")
                self._create_passage_between_adjacent_rooms(room, random.choice([r for r in self.map.rooms if r != room]))

        # 10. Go through each hallway, make sure each room has at least 2 passages to that space.
        for hallway in self.map.hallways:
            if hallway.count_passages(self.map) == 0:
                print(f"Hallway {hallway.identifier} has 0 passages. Adding connections.")
                self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[0])
                self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[1])

        for hallway in self.map.hallways:
            if hallway.count_passages(self.map) == 1:
                print(f"Hallway {hallway.identifier} has only 1 passage. Adding another.")
                if not any(p for p in self.map.passages if (p.side1.area_uid == hallway.unique_id and p.side2.area_uid == hallway.connects_rooms[1]) or \
                                                        (p.side2.area_uid == hallway.unique_id and p.side1.area_uid == hallway.connects_rooms[1])):
                    self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[1])
                else:
                    self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[0])
        
        # 11. Decorate rooms
        self._decorate_rooms()

        # 12. Decorate hallways
        self._decorate_hallways()

        self._decorate_walls()
        self._renumber_and_validate()
        
        print(f"Map generation complete with {len(self.map.rooms) + len(self.map.hallways)} areas.")
        return self.map

    def _is_area_free(self, x, y, width, height):
        """
        Checks if the given area is free.

        :param x: The x-coordinate of the top-left corner of the area.
        :param y: The y-coordinate of the top-left corner of the area.
        :param width: The width of the area.
        :param height: The height of the area.
        :return: True if the area is free, False otherwise.
        """
        for i in range(y, y + height):
            for j in range(x, x + width):
                if not (1 <= j <= self.map.width and 1 <= i <= self.map.height):
                    return False
                block = self.map.get_block_at(j, i)
                if block is None or not block.empty:
                    return False
        return True

    def _scatter_rooms(self, num_rooms):
        """
        Scatters rooms across the map.

        :param num_rooms: The number of rooms to scatter.
        """
        print("Scattering rooms...")
        
        if self.add_object:
            obj_type, x, y = self.add_object
            room_identifier = f"R{num_rooms + 1}" # Placeholder ID
            color_val = random.uniform(0.6, 0.9)
            
            placed = False
            for _ in range(self.placement_retries):
                room_width = random.randint(3, 8)
                room_height = random.randint(3, 8)
                room_min_x = x - random.randint(1, room_width - 2)
                room_min_y = y - random.randint(1, room_height - 2)

                if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                    new_room = Room(identifier=room_identifier, color=Color(color_val, color_val, color_val))
                    
                    blocks = []
                    for y_offset in range(room_height):
                        for x_offset in range(room_width):
                            # 3. Flip all of the room blocks to show they are not empty.
                            block = self.map.get_block_at(room_min_x + x_offset, room_min_y + y_offset)
                            block.area_uid = new_room.unique_id
                            block.empty = False
                            blocks.append(block)
                    
                    new_room.blocks = blocks
                    self.map.add_room(new_room)
                    placed = True
                    break
            if not placed:
                print(f"Warning: Could not place room for object at ({x},{y}).")
            else:
                num_rooms -= 1

        for i in range(num_rooms):
            room_identifier = f"R{i+1}"
            
            placed = False
            for _ in range(self.placement_retries):
                room_width = random.randint(3, 8)
                room_height = random.randint(3, 8)
                
                room_min_x = random.randint(1, self.map.width - room_width + 1)
                room_min_y = random.randint(1, self.map.height - room_height + 1)

                if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                    color_val = random.uniform(0.6, 0.9)
                    new_room = Room(identifier=room_identifier, color=Color(color_val, color_val, color_val))
                    
                    blocks = []
                    for y_coord in range(room_min_y, room_min_y + room_height):
                        for x_coord in range(room_min_x, room_min_x + room_width):
                            # 3. Flip all of the room blocks to show they are not empty.
                            block = self.map.get_block_at(x_coord, y_coord)
                            block.area_uid = new_room.unique_id
                            block.empty = False
                            blocks.append(block)
                    
                    new_room.blocks = blocks
                    self.map.add_room(new_room)
                    placed = True
                    break
            
            if not placed:
                print(f"Warning: Could not place room R{i+1}.")
        print(f"Successfully scattered {len(self.map.rooms)} rooms.")

    def _create_minimum_spanning_tree(self):
        """
        Creates a minimum spanning tree of the rooms.
        :return: A list of connections between rooms.
        """
        if len(self.map.rooms) < 2: return []
        
        nodes = self.map.rooms
        edges = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                center1 = get_center_of_blocks(nodes[i].blocks)
                center2 = get_center_of_blocks(nodes[j].blocks)
                dist = self._heuristic(center1, center2)
                edges.append((dist, nodes[i], nodes[j]))
        
        edges.sort(key=lambda edge: edge[0])
        
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
        Calculates the Manhattan distance between two points.

        :param a: The first point.
        :param b: The second point.
        :return: The Manhattan distance between the two points.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _find_path_astar(self, start, end):
        """
        Finds a path between two points using the A* algorithm.

        :param start: The start point.
        :param end: The end point.
        :return: A list of points representing the path, or None if no path is found.
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
                if block and not block.empty and neighbor_loc not in [start, end]:
                    cost = 100 

                tentative_g_score = g_score[current] + cost
                if tentative_g_score < g_score.get(neighbor_loc, float('inf')):
                    came_from[neighbor_loc] = current
                    g_score[neighbor_loc] = tentative_g_score
                    f_score[neighbor_loc] = tentative_g_score + self._heuristic(neighbor_loc, end)
                    heapq.heappush(open_set, (f_score[neighbor_loc], neighbor_loc))
        return None

    def _create_hallway_between_rooms(self, room1, room2):
        """
        Creates a hallway between two rooms.

        :param room1: The first room.
        :param room2: The second room.
        """
        start_block = random.choice(room1.blocks)
        end_block = random.choice(room2.blocks)
        
        path = self._find_path_astar((start_block.location.x, start_block.location.y), (end_block.location.x, end_block.location.y))
        
        if path:
            self.hallway_count += 1
            hallway_id = f"H{self.hallway_count}"
            new_hallway = Hallway(identifier=hallway_id, connects_rooms=(room1.unique_id, room2.unique_id))
            
            hallway_blocks = []
            for loc in path:
                block = self.map.get_block_at(loc[0], loc[1])
                if block and block.empty:
                    # 6. Flip all hallway blocks within the hallway to not empty.
                    block.area_uid = new_hallway.unique_id
                    block.empty = False
                    hallway_blocks.append(block)
            
            if hallway_blocks:
                color_val = random.uniform(0.4, 0.7)
                new_hallway.blocks = hallway_blocks
                new_hallway.color = Color(color_val, color_val, color_val)
                self.map.add_hallway(new_hallway)

    def _connect_rooms_with_hallways(self):
        """
        Connects rooms with hallways.
        """
        print("Connecting rooms with hallways...")
        if len(self.map.rooms) < 2: return

        connections = self._create_minimum_spanning_tree()
        print(f"MST determined {len(connections)} connections to be made.")

        for room1, room2 in connections:
            self._create_hallway_between_rooms(room1, room2)

    def _punch_passages(self):
        """
        Punches passages between adjacent non-empty blocks.
        """
        print("Punching passages...")
        for y in range(1, self.map.height + 1):
            for x in range(1, self.map.width + 1):
                block = self.map.get_block_at(x, y)
                if not block.empty:
                    for direction, (dx, dy) in {'north': (0, -1), 'east': (1, 0)}.items():
                        neighbor = self.map.get_block_at(x + dx, y + dy)
                        if neighbor and not neighbor.empty and block.area_uid != neighbor.area_uid:
                            if random.random() < PASSAGE_IS_DOOR:
                                passage = Passage(side1=block, side2=neighbor, is_door=True)
                            else:
                                passage = Passage(side1=block, side2=neighbor, is_door=False)
                            self.map.add_passage(passage)
                            setattr(block, direction, passage)
                            setattr(neighbor, {'north': 'south', 'east': 'west'}[direction], passage)

    def _create_passage_between_hallway_and_room(self, hallway, room_uid):
        """
        Creates a passage between a hallway and a room.

        :param hallway: The hallway.
        :param room_uid: The unique ID of the room.
        :return: True if a passage was created, False otherwise.
        """
        wall_candidates = []
        for h_block in hallway.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor_loc = (h_block.location.x + dx, h_block.location.y + dy)
                neighbor = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                if neighbor and neighbor.area_uid == room_uid and isinstance(getattr(h_block, direction), Wall):
                    wall_candidates.append((h_block, neighbor, direction))
        
        if wall_candidates:
            h_block, r_block, direction = random.choice(wall_candidates)
            passage = Passage(side1=h_block, side2=r_block, is_door=True)
            setattr(h_block, direction, passage)
            setattr(r_block, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction], passage)
            self.map.add_passage(passage)
            return True
        return False

    def _create_passage_between_adjacent_rooms(self, room1, room2):
        """
        Creates a passage between two adjacent rooms.

        :param room1: The first room.
        :param room2: The second room.
        :return: True if a passage was created, False otherwise.
        """
        wall_candidates = []
        for r1_block in room1.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor_loc = (r1_block.location.x + dx, r1_block.location.y + dy)
                neighbor = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                if neighbor and neighbor.area_uid == room2.unique_id and isinstance(getattr(r1_block, direction), Wall):
                    wall_candidates.append((r1_block, neighbor, direction))
        
        if wall_candidates:
            r1_block, r2_block, direction = random.choice(wall_candidates)
            passage = Passage(side1=r1_block, side2=r2_block, is_door=True)
            setattr(r1_block, direction, passage)
            setattr(r2_block, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction], passage)
            self.map.add_passage(passage)
            return True
        return False

    def _decorate_rooms(self):
        """
        Decorates the rooms on the map.
        """
        print("Decorating rooms...")
        if self.add_object:
            obj_type, x, y = self.add_object
            area = self.map.get_area_by_location(x, y)
            if area:
                area.decorate(self.map, forced_object=(obj_type, (x,y)))

        for room in self.map.rooms:
            if not self.add_object or self.map.get_area_by_location(self.add_object[1], self.add_object[2]) != room:
                room.decorate(self.map)

    def _decorate_hallways(self):
        """
        Decorates the hallways on the map.
        """
        print("Decorating hallways...")
        for hallway in self.map.hallways:
            hallway.decorate(self.map)

    def _decorate_walls(self):
        """
        Decorates the walls on the map.
        """
        print("Decorating walls...")
        all_walls = set()
        for block in self.map.blocks.values():
            for direction in ['north', 'south', 'east', 'west']:
                if isinstance(getattr(block, direction), Wall):
                    all_walls.add((block, direction))
        
        processed_blocks = set()
        for block, direction in all_walls:
            if block.unique_id in processed_blocks:
                continue

            segment = [block.location]
            
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
            else:
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

            if random.random() < WALL_DECORATION_CHANCE:
                desc = random.choice(WALL_DECORATIONS)
                decoration = WallDecoration(locations=segment, direction=direction, description=desc, area_uid=block.area_uid)
                self.map.add_wall_decoration(decoration)

    def _renumber_and_validate(self):
        """
        Renumbers and validates the map.
        """
        print("Renumbering and validating map...")
        
        all_areas = sorted(self.map.rooms + self.map.hallways, key=lambda a: (get_center_of_blocks(a.blocks)[1], -get_center_of_blocks(a.blocks)[0]), reverse=True)
        
        for i, area in enumerate(all_areas):
            area.rename(f"Area {i+1}")

        self.map.rooms = [area for area in all_areas if isinstance(area, Room)]
        self.map.hallways = [area for area in all_areas if isinstance(area, Hallway)]

        print("Validation complete.")