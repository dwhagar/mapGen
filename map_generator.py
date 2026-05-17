import random
import math
import heapq
from .map.map import Map
from .map.room import Room
from .map.hallway import Hallway
from .map.block import Block
from .map.wall import Wall
from .map.passage import Passage


class MapGenerator:
    def __init__(self, placement_retries=10):
        self.map = Map()
        self.placement_retries = placement_retries

    def generate(self):
        print("Starting map generation...")
        num_rooms = random.randint(self.map.MIN_ROOMS, self.map.MAX_ROOMS)
        print(f"Attempting to generate {num_rooms} rooms.")

        self._scatter_rooms(num_rooms)
        self._connect_rooms_with_hallways()
        self._finalize_map()
        
        print(f"Map generation complete with {len(self.map.rooms)} rooms.")
        return self.map

    def _find_grid_layout(self, num_items):
        cols = int(math.ceil(math.sqrt(num_items)))
        rows = int(math.ceil(num_items / cols))
        return rows, cols

    def _is_area_free(self, x, y, width, height):
        """Checks if a rectangular area is free, allowing for shared walls."""
        for i in range(y, y + height):
            for j in range(x, x + width):
                if not (0 <= j <= self.map.MAX_X and 0 <= i <= self.map.MAX_Y):
                    return False
                if self.map.get_block_at(j, i) is not None:
                    return False
        return True

    def _scatter_rooms(self, num_rooms):
        print("Scattering rooms...")
        rows, cols = self._find_grid_layout(num_rooms)
        partition_width = self.map.MAX_X // cols
        partition_height = self.map.MAX_Y // rows
        
        room_count = 0
        for row in range(rows):
            for col in range(cols):
                if room_count >= num_rooms: break
                
                part_min_x = col * partition_width
                part_max_x = part_min_x + partition_width
                part_min_y = row * partition_height
                part_max_y = part_min_y + partition_height

                placed = False
                for _ in range(self.placement_retries):
                    room_width = random.randint(3, max(4, partition_width - 1))
                    room_height = random.randint(3, max(4, partition_height - 1))
                    
                    room_min_x = random.randint(part_min_x, part_max_x - room_width)
                    room_min_y = random.randint(part_min_y, part_max_y - room_height)

                    if self._is_area_free(room_min_x, room_min_y, room_width, room_height):
                        room_identifier = f"room_{room_count}"
                        new_room = Room(identifier=room_identifier)
                        
                        blocks = []
                        for y in range(room_min_y, room_min_y + room_height):
                            for x in range(room_min_x, room_min_x + room_width):
                                block = Block(location=(x, y), room_identifier=room_identifier)
                                blocks.append(block)
                        
                        new_room.blocks = blocks
                        self.map.add_room(new_room)
                        room_count += 1
                        placed = True
                        break
                
                if not placed:
                    print(f"Warning: Could not place a room in partition ({row}, {col}).")
        print(f"Successfully scattered {len(self.map.rooms)} rooms.")

    def _get_room_center(self, room):
        if not room.blocks: return None
        x_coords = [b.location[0] for b in room.blocks]
        y_coords = [b.location[1] for b in room.blocks]
        return (sum(x_coords) // len(x_coords), sum(y_coords) // len(y_coords))

    def _create_minimum_spanning_tree(self):
        if not self.map.rooms: return []
        
        nodes = self.map.rooms
        edges = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                center1 = self._get_room_center(nodes[i])
                center2 = self._get_room_center(nodes[j])
                dist = self._heuristic(center1, center2)
                edges.append((dist, nodes[i], nodes[j]))
        
        edges.sort()
        
        parent = {room: room for room in nodes}
        def find_set(room):
            if parent[room] == room: return room
            parent[room] = find_set(parent[room])
            return parent[room]
        def unite_sets(a, b):
            a = find_set(a)
            b = find_set(b)
            if a != b: parent[b] = a

        mst_connections = []
        for dist, room1, room2 in edges:
            if find_set(room1) != find_set(room2):
                unite_sets(room1, room2)
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
            for loc in path:
                if self.map.get_block_at(loc[0], loc[1]) is None:
                    block = Block(location=loc, room_identifier='hallway')
                    self.map.blocks[loc] = block

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
            x, y = block.location
            
            directions = {'north': (x, y - 1), 'east': (x + 1, y), 'south': (x, y + 1), 'west': (x - 1, y)}
            
            for direction, (nx, ny) in directions.items():
                if getattr(block, direction) is None:
                    neighbor = self.map.get_block_at(nx, ny)
                    
                    if neighbor:
                        # If neighbor is in a different room, it's a wall.
                        if block.room_identifier != neighbor.room_identifier and \
                           'room' in block.room_identifier and 'room' in neighbor.room_identifier:
                            setattr(block, direction, Wall())
                        # Otherwise, it's a passage.
                        else:
                            passage = Passage(side1=block, side2=neighbor)
                            setattr(block, direction, passage)
                            # Set the corresponding attribute on the neighbor
                            opposite = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
                            setattr(neighbor, opposite[direction], passage)
                    else:
                        # No neighbor, so it's an exterior wall.
                        setattr(block, direction, Wall())

if __name__ == '__main__':
    generator = MapGenerator()
    generated_map = generator.generate()
