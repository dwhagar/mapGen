import random
import math
import heapq
from reportlab.lib.colors import Color

from .map import Map
from .room import Room
from .hallway import Hallway
from .block import Block
from .wall import Wall
from .passage import Passage
from .wall_decoration import WallDecoration
from .utils import get_center_of_blocks
from .constants import WALL_DECORATION_CHANCE
from .text import WALL_DECORATIONS

class Generator:
    def __init__(self, placement_retries=10):
        self.map = Map()
        self.placement_retries = placement_retries
        self.hallway_count = 0

    def generate(self):
        print("Starting map generation...")
        num_rooms = random.randint(self.map.MIN_ROOMS, self.map.MAX_ROOMS)
        print(f"Attempting to generate {num_rooms} rooms.")

        self._scatter_rooms(num_rooms)
        self._connect_rooms_with_hallways()
        self._finalize_map()
        self._punch_doors()
        self._decorate_map()
        self._decorate_walls()
        self._renumber_and_validate()
        
        print(f"Map generation complete with {len(self.map.rooms) + len(self.map.hallways)} areas.")
        return self.map

    def _is_area_free(self, x, y, width, height):
        for i in range(y, y + height):
            for j in range(x, x + width):
                if not (0 <= j <= self.map.MAX_X and 0 <= i <= self.map.MAX_Y):
                    return False
                if self.map.get_block_at(j, i) is not None:
                    return False
        return True

    def _scatter_rooms(self, num_rooms):
        print("Scattering rooms...")
        
        for i in range(num_rooms):
            room_identifier = f"R{i+1}"
            
            placed = False
            for _ in range(self.placement_retries):
                room_width = random.randint(3, 8)
                room_height = random.randint(3, 8)
                
                room_min_x = random.randint(0, self.map.MAX_X - room_width)
                room_min_y = random.randint(0, self.map.MAX_Y - room_height)

                if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                    color_val = random.uniform(0.6, 0.9)
                    new_room = Room(identifier=room_identifier, color=Color(color_val, color_val, color_val))
                    
                    blocks = []
                    for y in range(room_min_y, room_min_y + room_height):
                        for x in range(room_min_x, room_min_x + room_width):
                            block = Block(location=(x, y), room_identifier=room_identifier)
                            blocks.append(block)
                    
                    new_room.blocks = blocks
                    self.map.add_room(new_room)
                    placed = True
                    break
            
            if not placed:
                print(f"Warning: Could not place room R{i+1}.")
        print(f"Successfully scattered {len(self.map.rooms)} rooms.")

    def _create_minimum_spanning_tree(self):
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
        
        parent = {room.identifier: room.identifier for room in nodes}
        def find_set(room_id):
            if parent[room_id] == room_id: return room_id
            parent[room_id] = find_set(parent[room_id])
            return parent[room_id]
        def unite_sets(id1, id2):
            id1 = find_set(id1)
            id2 = find_set(id2)
            if id1 != id2: parent[id2] = id1

        mst_connections = []
        for dist, room1, room2 in edges:
            if find_set(room1.identifier) != find_set(room2.identifier):
                unite_sets(room1.identifier, room2.identifier)
                mst_connections.append((room1, room2))
        return mst_connections

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _find_path_astar(self, start, end):
        open_set = [(0, start)]
        came_from = {}
        g_score = { (x, y): float('inf') for x in range(self.map.MAX_X + 1) for y in range(self.map.MAX_Y + 1) }
        g_score[start] = 0
        f_score = { (x, y): float('inf') for x in range(self.map.MAX_X + 1) for y in range(self.map.MAX_Y + 1) }
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
                if not (0 <= neighbor_loc[0] <= self.map.MAX_X and 0 <= neighbor_loc[1] <= self.map.MAX_Y):
                    continue

                cost = 1
                if self.map.get_block_at(neighbor_loc[0], neighbor_loc[1]) and neighbor_loc not in [start, end]:
                    cost = 100 

                tentative_g_score = g_score[current] + cost
                if tentative_g_score < g_score.get(neighbor_loc, float('inf')):
                    came_from[neighbor_loc] = current
                    g_score[neighbor_loc] = tentative_g_score
                    f_score[neighbor_loc] = tentative_g_score + self._heuristic(neighbor_loc, end)
                    heapq.heappush(open_set, (f_score[neighbor_loc], neighbor_loc))
        return None

    def _create_hallway_between_rooms(self, room1, room2):
        start_block = random.choice(room1.blocks)
        end_block = random.choice(room2.blocks)
        
        path = self._find_path_astar(start_block.location, end_block.location)
        
        if path:
            self.hallway_count += 1
            hallway_id = f"H{self.hallway_count}"
            hallway_blocks = []
            for loc in path:
                if self.map.get_block_at(loc[0], loc[1]) is None:
                    block = Block(location=loc, room_identifier=hallway_id)
                    hallway_blocks.append(block)
            
            if hallway_blocks:
                color_val = random.uniform(0.4, 0.7)
                new_hallway = Hallway(identifier=hallway_id, connects_rooms=(room1.identifier, room2.identifier), blocks=hallway_blocks, color=Color(color_val, color_val, color_val))
                self.map.add_hallway(new_hallway)

    def _connect_rooms_with_hallways(self):
        print("Connecting rooms with hallways...")
        if len(self.map.rooms) < 2: return

        connections = self._create_minimum_spanning_tree()
        print(f"MST determined {len(connections)} connections to be made.")

        for room1, room2 in connections:
            self._create_hallway_between_rooms(room1, room2)

    def _finalize_map(self):
        print("Finalizing map by placing walls and passages...")
        all_blocks = list(self.map.blocks.values())
        for block in all_blocks:
            block.check_adjacent(self.map)

    def _punch_doors(self):
        print("Punching doors...")
        
        for hallway in self.map.hallways:
            self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[0])
            self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[1])

        for i in range(len(self.map.rooms)):
            for j in range(i + 1, len(self.map.rooms)):
                self._create_passage_between_adjacent_rooms(self.map.rooms[i], self.map.rooms[j])

        for hallway in self.map.hallways:
            passage_count = sum(1 for p in self.map.passages if p.side1.room_identifier == hallway.identifier or p.side2.room_identifier == hallway.identifier)
            
            if passage_count < 2:
                print(f"Hallway {hallway.identifier} has only {passage_count} passage. Adding more.")
                
                if not any(p for p in self.map.passages if (p.side1.room_identifier == hallway.identifier and p.side2.room_identifier == hallway.connects_rooms[1]) or \
                                                        (p.side2.room_identifier == hallway.identifier and p.side1.room_identifier == hallway.connects_rooms[1])):
                    self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[1])

                passage_count = sum(1 for p in self.map.passages if p.side1.room_identifier == hallway.identifier or p.side2.room_identifier == hallway.identifier)
                if passage_count < 2:
                    self._create_passage_between_hallway_and_room(hallway, hallway.connects_rooms[0])

    def _create_passage_between_hallway_and_room(self, hallway, room_id):
        wall_candidates = []
        for h_block in hallway.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor_loc = (h_block.location[0] + dx, h_block.location[1] + dy)
                neighbor = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                if neighbor and neighbor.room_identifier == room_id and isinstance(getattr(h_block, direction), Wall):
                    wall_candidates.append((h_block, neighbor, direction))
        
        if wall_candidates:
            h_block, r_block, direction = random.choice(wall_candidates)
            passage = Passage(side1=h_block, side2=r_block, is_door=True)
            setattr(h_block, direction, passage)
            setattr(r_block, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction], passage)
            self.map.add_passage(passage)

    def _create_passage_between_adjacent_rooms(self, room1, room2):
        wall_candidates = []
        for r1_block in room1.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor_loc = (r1_block.location[0] + dx, r1_block.location[1] + dy)
                neighbor = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                if neighbor and neighbor.room_identifier == room2.identifier and isinstance(getattr(r1_block, direction), Wall):
                    wall_candidates.append((r1_block, neighbor, direction))
        
        if wall_candidates:
            r1_block, r2_block, direction = random.choice(wall_candidates)
            passage = Passage(side1=r1_block, side2=r2_block, is_door=True)
            setattr(r1_block, direction, passage)
            setattr(r2_block, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction], passage)
            self.map.add_passage(passage)

    def _decorate_map(self):
        print("Decorating map with items, objects, and encounters...")
        for room in self.map.rooms:
            room.decorate()
        for hallway in self.map.hallways:
            hallway.decorate()

    def _decorate_walls(self):
        print("Decorating walls...")
        all_walls = set()
        for block in self.map.blocks.values():
            for direction in ['north', 'south', 'east', 'west']:
                if isinstance(getattr(block, direction), Wall):
                    all_walls.add((block.location, direction))
        
        while all_walls:
            start_loc, direction = all_walls.pop()
            segment = [start_loc]
            
            if direction in ['north', 'south']:
                curr_loc = (start_loc[0], start_loc[1] - 1)
                while (curr_loc, direction) in all_walls:
                    segment.append(curr_loc)
                    all_walls.remove((curr_loc, direction))
                    curr_loc = (curr_loc[0], curr_loc[1] - 1)
                curr_loc = (start_loc[0], start_loc[1] + 1)
                while (curr_loc, direction) in all_walls:
                    segment.append(curr_loc)
                    all_walls.remove((curr_loc, direction))
                    curr_loc = (curr_loc[0], curr_loc[1] + 1)
            else:
                curr_loc = (start_loc[0] - 1, start_loc[1])
                while (curr_loc, direction) in all_walls:
                    segment.append(curr_loc)
                    all_walls.remove((curr_loc, direction))
                    curr_loc = (curr_loc[0] - 1, curr_loc[1])
                curr_loc = (start_loc[0] + 1, start_loc[1])
                while (curr_loc, direction) in all_walls:
                    segment.append(curr_loc)
                    all_walls.remove((curr_loc, direction))
                    curr_loc = (curr_loc[0] + 1, curr_loc[1])

            if random.random() < WALL_DECORATION_CHANCE:
                desc = random.choice(WALL_DECORATIONS)
                decoration = WallDecoration(locations=segment, direction=direction, description=desc)
                self.map.add_wall_decoration(decoration)

    def _renumber_and_validate(self):
        print("Renumbering and validating map...")
        
        all_areas = self.map.rooms + self.map.hallways
        for i, area in enumerate(all_areas):
            area.rename(f"Area {i+1}")
            
        block_owners = {}
        for area in all_areas:
            for block in area.blocks:
                if block.location in block_owners:
                    print(f"Warning: Block at {block.location} is in multiple spaces: {block_owners[block.location]} and {area.identifier}")
                block_owners[block.location] = area.identifier
        
        self.map.connectivity = {}
        for passage in self.map.passages:
            id1 = passage.side1.room_identifier
            id2 = passage.side2.room_identifier
            self.map.add_connection(id1, id2)

        print("Validation complete.")