import random
import math
import heapq
import argparse
from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, red, blue, green, white, Color
from reportlab.lib.units import mm

from map.map import Map
from map.room import Room
from map.hallway import Hallway
from map.block import Block
from map.wall import Wall
from map.passage import Passage, Door, DOOR_STATUS_SECRET, DOOR_STATUS_TRAPPED, DOOR_STATUS_LOCKED, DOOR_STATUS_CLOSED, DOOR_STATUS_OPEN
from map.item import Item
from map.object import MapObject
from map.encounter import Encounter
from map.texture import draw_door_symbol, draw_secret_door_symbol, draw_trapped_door_symbol

class MapGenerator:
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
        
        print(f"Map generation complete with {len(self.map.rooms)} rooms.")
        return self.map

    def _draw_legend(self, c, start_x, start_y, block_size):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(start_x, start_y, "Map Legend")
        y_pos = start_y - 30
        c.setFont("Helvetica", 10)

        def draw_entry(label, color, shape_func):
            nonlocal y_pos
            c.setFillColor(color)
            shape_func(c, start_x, y_pos, block_size)
            c.setFillColor(black)
            c.drawString(start_x + block_size + 10, y_pos + (block_size/4), label)
            y_pos -= 30

        draw_entry("Floor", Color(0.8, 0.8, 0.8), lambda c, x, y, s: c.rect(x, y, s, s, fill=1))
        draw_entry("Item", blue, lambda c, x, y, s: c.circle(x + s/2, y + s/2, s/4, fill=1))
        draw_entry("Map Object", red, lambda c, x, y, s: c.rect(x + s/4, y + s/4, s/2, s/2, fill=1))
        draw_entry("Encounter", green, lambda c, x, y, s: self._draw_triangle(c, x, y, s))
        draw_entry("Wall", black, lambda c, x, y, s: c.rect(x, y + s*0.4, s, s*0.2, fill=1))
        
        def draw_door_legend(c, x, y, s):
            c.setFillColor(black)
            c.rect(x, y + s*0.4, s, s*0.2, fill=1)
            draw_door_symbol(c, x + s/2, y + s/2, s, 'horizontal')
        draw_entry("Door", green, draw_door_legend)

        draw_entry("Door (Secret)", green, lambda c, x, y, s: draw_secret_door_symbol(c, x, y, s))
        draw_entry("Door (Trapped)", green, lambda c, x, y, s: draw_trapped_door_symbol(c, x, y, s))

    def _draw_triangle(self, c, x, y, s):
        p = c.beginPath()
        p.moveTo(x + s/2, y + s*0.8)
        p.lineTo(x + s*0.2, y + s*0.2)
        p.lineTo(x + s*0.8, y + s*0.2)
        c.drawPath(p, fill=1, stroke=0)

    def save_to_pdf(self, filename):
        print(f"Saving map to {filename}...")
        c = canvas.Canvas(filename, pagesize=pagesizes.A4)
        width, height = pagesizes.A4
        block_size_mm = 6.35
        block_size_pts = block_size_mm * mm
        margin = 20 * mm

        map_width_pts = (self.map.MAX_X + 1) * block_size_pts
        map_height_pts = (self.map.MAX_Y + 1) * block_size_pts
        x_offset = margin
        y_offset = height - margin - map_height_pts

        for (x, y), block in self.map.blocks.items():
            draw_x = x_offset + x * block_size_pts
            draw_y = y_offset + (self.map.MAX_Y - y) * block_size_pts
            
            container = self.map.get_room_by_identifier(block.room_identifier) or self.map.get_hallway_by_identifier(block.room_identifier)
            if container and container.color:
                c.setFillColor(container.color)
            else:
                c.setFillColor(Color(0.8, 0.8, 0.8))
            c.rect(draw_x, draw_y, block_size_pts, block_size_pts, fill=1, stroke=0)

        for (x, y), block in self.map.blocks.items():
            draw_x = x_offset + x * block_size_pts
            draw_y = y_offset + (self.map.MAX_Y - y) * block_size_pts
            for content in block.contents:
                if isinstance(content, Item):
                    c.setFillColor(blue)
                    c.circle(draw_x + block_size_pts / 2, draw_y + block_size_pts / 2, block_size_pts / 4, fill=1, stroke=0)
                elif isinstance(content, MapObject):
                    c.setFillColor(red)
                    c.rect(draw_x + block_size_pts / 4, draw_y + block_size_pts / 4, block_size_pts / 2, block_size_pts / 2, fill=1, stroke=0)
                elif isinstance(content, Encounter):
                    c.setFillColor(green)
                    self._draw_triangle(c, draw_x, draw_y, block_size_pts)

        c.setStrokeColor(black)
        c.setLineWidth(0.1)
        for i in range(self.map.MAX_X + 2):
            c.line(x_offset + i * block_size_pts, y_offset, x_offset + i * block_size_pts, y_offset + map_height_pts)
        for i in range(self.map.MAX_Y + 2):
            c.line(x_offset, y_offset + i * block_size_pts, x_offset + map_width_pts, y_offset + i * block_size_pts)

        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.setLineCap(1)
        for block in self.map.blocks.values():
            x, y = block.location
            draw_x = x_offset + x * block_size_pts
            draw_y = y_offset + (self.map.MAX_Y - y) * block_size_pts
            
            if isinstance(block.north, Wall): c.line(draw_x, draw_y + block_size_pts, draw_x + block_size_pts, draw_y + block_size_pts)
            if isinstance(block.south, Wall): c.line(draw_x, draw_y, draw_x + block_size_pts, draw_y)
            if isinstance(block.east, Wall): c.line(draw_x + block_size_pts, draw_y, draw_x + block_size_pts, draw_y + block_size_pts)
            if isinstance(block.west, Wall): c.line(draw_x, draw_y, draw_x, draw_y + block_size_pts)

        for passage in self.map.passages:
            if not passage.is_door: continue
            
            block1, block2 = passage.side1, passage.side2
            
            draw_x = x_offset + ((block1.location[0] + block2.location[0]) / 2) * block_size_pts
            draw_y = y_offset + (self.map.MAX_Y - ((block1.location[1] + block2.location[1]) / 2)) * block_size_pts
            
            status = passage.door_status
            if status == DOOR_STATUS_SECRET:
                draw_secret_door_symbol(c, draw_x, draw_y, block_size_pts)
            elif status == DOOR_STATUS_TRAPPED:
                draw_trapped_door_symbol(c, draw_x, draw_y, block_size_pts)
            elif status in [DOOR_STATUS_CLOSED, DOOR_STATUS_LOCKED]:
                draw_door_symbol(c, draw_x, draw_y, block_size_pts, passage.orientation)

        c.setFont("Helvetica", 8)
        for i in range(self.map.MAX_X + 1):
            c.drawCentredString(x_offset + (i + 0.5) * block_size_pts, y_offset + map_height_pts + 5, str(i))
        for i in range(self.map.MAX_Y + 1):
            c.drawRightString(x_offset - 5, y_offset + (self.map.MAX_Y - i + 0.5) * block_size_pts, str(i))

        c.showPage()
        self._draw_legend(c, margin, height - margin, block_size_pts)
        
        c.showPage()
        c.setFont("Helvetica", 10)
        text_object = c.beginText(margin, height - margin)
        text_object.textLine("Map Connectivity Graph:")
        text_object.textLine("")
        for key, connections in self.map.connectivity.items():
            text_object.textLine(f"{key} connects to: {', '.join(connections)}")
        c.drawText(text_object)

        c.save()
        print("PDF saved successfully.")

    def _find_grid_layout(self, num_items):
        cols = int(math.ceil(math.sqrt(num_items)))
        rows = int(math.ceil(num_items / cols))
        return rows, cols

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

    def _get_room_center(self, room):
        if not room.blocks: return None
        x_coords = [b.location[0] for b in room.blocks]
        y_coords = [b.location[1] for b in room.blocks]
        return (sum(x_coords) // len(x_coords), sum(y_coords) // len(y_coords))

    def _create_minimum_spanning_tree(self):
        if len(self.map.rooms) < 2: return []
        
        nodes = self.map.rooms
        edges = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                center1 = self._get_room_center(nodes[i])
                center2 = self._get_room_center(nodes[j])
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
            room1_id, room2_id = hallway.connects_rooms
            
            wall_candidates1 = []
            for h_block in hallway.blocks:
                for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                    neighbor_loc = (h_block.location[0] + dx, h_block.location[1] + dy)
                    neighbor = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                    if neighbor and neighbor.room_identifier == room1_id and isinstance(getattr(h_block, direction), Wall):
                        wall_candidates1.append((h_block, neighbor, direction))
            
            wall_candidates2 = []
            for h_block in hallway.blocks:
                for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                    neighbor_loc = (h_block.location[0] + dx, h_block.location[1] + dy)
                    neighbor = self.map.get_block_at(neighbor_loc[0], neighbor_loc[1])
                    if neighbor and neighbor.room_identifier == room2_id and isinstance(getattr(h_block, direction), Wall):
                        wall_candidates2.append((h_block, neighbor, direction))

            if wall_candidates1:
                h_block, r_block, direction = random.choice(wall_candidates1)
                passage = Passage(side1=h_block, side2=r_block, is_door=True)
                passage.orientation = 'horizontal' if direction in ['north', 'south'] else 'vertical'
                setattr(h_block, direction, passage)
                setattr(r_block, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction], passage)
                self.map.add_passage(passage)
                self.map.add_connection(h_block.room_identifier, r_block.room_identifier)

            if wall_candidates2:
                h_block, r_block, direction = random.choice(wall_candidates2)
                passage = Passage(side1=h_block, side2=r_block, is_door=True)
                passage.orientation = 'horizontal' if direction in ['north', 'south'] else 'vertical'
                setattr(h_block, direction, passage)
                setattr(r_block, {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[direction], passage)
                self.map.add_passage(passage)
                self.map.add_connection(h_block.room_identifier, r_block.room_identifier)

    def _decorate_map(self):
        print("Decorating map with items, objects, and encounters...")
        for room in self.map.rooms:
            room.decorate()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a random RPG map.')
    parser.add_argument('-p', '--print', dest='filename', nargs='?', const='map.pdf', default=None,
                        help='Output the map to a PDF file. Defaults to map.pdf if no filename is provided.')
    
    args = parser.parse_args()

    generator = MapGenerator()
    generated_map = generator.generate()
    
    if args.filename:
        generator.save_to_pdf(args.filename)
