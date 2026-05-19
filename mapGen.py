import argparse
from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, red, blue, green, white, Color
from reportlab.lib.units import mm
import math
from collections import defaultdict
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from map.generator import Generator
from map.item import Item
from map.object import MapObject
from map.encounter import Encounter
from map.wall import Wall
from map.texture import draw_door_symbol, draw_secret_door_symbol, draw_trapped_door_symbol
from map.constants import DOOR_STATUS_SECRET, DOOR_STATUS_TRAPPED, DOOR_STATUS_LOCKED, DOOR_STATUS_CLOSED
from map.utils import get_center_of_blocks

def _get_wall_direction_string(wall_segment, room_center):
    wall_center_x = sum(loc[0] for loc in wall_segment) / len(wall_segment)
    wall_center_y = sum(loc[1] for loc in wall_segment) / len(wall_segment)
    
    dx = wall_center_x - room_center[0]
    dy = wall_center_y - room_center[1]

    if abs(dx) < 2 and abs(dy) < 2:
        return "central"

    if dy > abs(dx):
        return "northern"
    elif dy < -abs(dx):
        return "southern"
    elif dx > abs(dy):
        return "eastern"
    else:
        return "western"

class PdfGenerator:
    def __init__(self, map_instance, include_index=True):
        self.map = map_instance
        self.coord_table = {}
        self.include_index = include_index

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

        def draw_secret_door_legend(c, x, y, s):
            c.setFillColor(black)
            c.rect(x, y + s*0.4, s, s*0.2, fill=1)
            draw_secret_door_symbol(c, x + s/2, y + s/2, s, 'horizontal')
        draw_entry("Door (Secret)", blue, draw_secret_door_legend)

        def draw_trapped_door_legend(c, x, y, s):
            c.setFillColor(black)
            c.rect(x, y + s*0.4, s, s*0.2, fill=1)
            draw_trapped_door_symbol(c, x + s/2, y + s/2, s, 'horizontal')
        draw_entry("Door (Trapped)", red, draw_trapped_door_legend)
        
        return y_pos

    def _draw_triangle(self, c, x, y, s):
        p = c.beginPath()
        p.moveTo(x + s/2, y + s*0.8)
        p.lineTo(x + s*0.2, y + s*0.2)
        p.lineTo(x + s*0.8, y + s*0.2)
        c.drawPath(p, fill=1, stroke=0)

    def _build_coordinate_translation_table(self, pagesize, margin, block_size_pts):
        width, height = pagesize
        map_width_pts = (self.map.MAX_X + 1) * block_size_pts
        map_height_pts = (self.map.MAX_Y + 1) * block_size_pts
        x_offset = margin
        y_offset = height - margin - map_height_pts

        for y_grid in range(self.map.MAX_Y + 1):
            for x_grid in range(self.map.MAX_X + 1):
                bl_x = x_offset + x_grid * block_size_pts
                bl_y = y_offset + (self.map.MAX_Y - y_grid) * block_size_pts
                self.coord_table[(x_grid, y_grid)] = {
                    'bl': (bl_x, bl_y),
                    'br': (bl_x + block_size_pts, bl_y),
                    'tl': (bl_x, bl_y + block_size_pts),
                    'tr': (bl_x + block_size_pts, bl_y + block_size_pts)
                }

    def _draw_index(self, c, start_x, start_y, page_height, margin):
        styles = getSampleStyleSheet()
        style_body = styles['BodyText']
        style_heading = styles['h2']
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(start_x, start_y, "Map Index")
        
        y_pos = start_y - 30
        
        all_locations = self.map.rooms + self.map.hallways
        sorted_locations = sorted(all_locations, key=lambda x: int(''.join(filter(str.isdigit, x.identifier))))

        for loc in sorted_locations:
            wall_decos_by_direction = defaultdict(list)
            for deco in self.map.wall_decorations:
                if deco.get_room_identifier(self.map) == loc.identifier:
                    room_center = get_center_of_blocks(loc.blocks)
                    direction_str = _get_wall_direction_string(deco.locations, room_center)
                    wall_decos_by_direction[direction_str].append(deco.description)

            if not loc.contents and not wall_decos_by_direction:
                continue
            
            p = Paragraph(f"{loc.identifier}:", style_heading)
            p_w, p_h = p.wrapOn(c, 500, 50)
            if y_pos - p_h < margin:
                c.showPage()
                y_pos = page_height - margin
            p.drawOn(c, start_x, y_pos - p_h)
            y_pos -= p_h

            for content in loc.contents:
                p = Paragraph(f"  - {content.description}", style_body)
                p_w, p_h = p.wrapOn(c, 480, 50)
                if y_pos - p_h < margin:
                    c.showPage()
                    y_pos = page_height - margin
                p.drawOn(c, start_x + 20, y_pos - p_h)
                y_pos -= p_h

            for direction, descriptions in wall_decos_by_direction.items():
                desc_str = " and ".join(descriptions)
                p = Paragraph(f"  - On the {direction} wall, you see {desc_str}.", style_body)
                p_w, p_h = p.wrapOn(c, 480, 50)
                if y_pos - p_h < margin:
                    c.showPage()
                    y_pos = page_height - margin
                p.drawOn(c, start_x + 20, y_pos - p_h)
                y_pos -= p_h
            
            y_pos -= 10

    def _find_closest_block(self, center, blocks):
        closest_block = None
        min_dist = float('inf')
        for block in blocks:
            dist = math.sqrt((center[0] - block.location[0])**2 + (center[1] - block.location[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest_block = block
        return closest_block

    def save_to_pdf(self, filename):
        print(f"Saving map to {filename}...")
        c = canvas.Canvas(filename, pagesize=pagesizes.A4)
        width, height = pagesizes.A4
        block_size_mm = 6.35
        block_size_pts = block_size_mm * mm
        margin = 20 * mm

        self._build_coordinate_translation_table((width, height), margin, block_size_pts)

        for (x, y), block in self.map.blocks.items():
            draw_x, draw_y = self.coord_table[(x, y)]['bl']
            
            container = self.map.get_area_by_identifier(block.room_identifier)
            if container and container.color:
                c.setFillColor(container.color)
            else:
                c.setFillColor(Color(0.8, 0.8, 0.8))
            c.rect(draw_x, draw_y, block_size_pts, block_size_pts, fill=1, stroke=0)

        for (x, y), block in self.map.blocks.items():
            draw_x, draw_y = self.coord_table[(x, y)]['bl']
            for content in block.contents:
                if isinstance(content, MapObject):
                    c.setFillColor(red)
                    c.rect(draw_x + block_size_pts / 4, draw_y + block_size_pts / 4, block_size_pts / 2, block_size_pts / 2, fill=1, stroke=0)
                elif isinstance(content, Encounter):
                    c.setFillColor(green)
                    self._draw_triangle(c, draw_x, draw_y, block_size_pts)
                elif isinstance(content, Item):
                    c.setFillColor(blue)
                    c.circle(draw_x + block_size_pts / 2, draw_y + block_size_pts / 2, block_size_pts / 4, fill=1, stroke=0)

        c.setStrokeColor(black)
        c.setLineWidth(0.1)
        grid_x_start, grid_y_start = self.coord_table[(0,0)]['tl']
        grid_end_x = self.coord_table[(self.map.MAX_X, 0)]['tr'][0]
        grid_end_y = self.coord_table[(0, self.map.MAX_Y)]['bl'][1]
        for i in range(self.map.MAX_X + 2):
            c.line(grid_x_start + i * block_size_pts, grid_y_start, grid_x_start + i * block_size_pts, grid_end_y)
        for i in range(self.map.MAX_Y + 2):
            c.line(grid_x_start, grid_y_start - i * block_size_pts, grid_end_x, grid_y_start - i * block_size_pts)

        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.setLineCap(1)
        for block in self.map.blocks.values():
            corners = self.coord_table[block.location]
            
            if isinstance(block.north, Wall): c.line(corners['tl'][0], corners['tl'][1], corners['tr'][0], corners['tr'][1])
            if isinstance(block.south, Wall): c.line(corners['bl'][0], corners['bl'][1], corners['br'][0], corners['br'][1])
            if isinstance(block.east, Wall): c.line(corners['br'][0], corners['br'][1], corners['tr'][0], corners['tr'][1])
            if isinstance(block.west, Wall): c.line(corners['bl'][0], corners['bl'][1], corners['tl'][0], corners['tl'][1])

        for passage in self.map.passages:
            if not passage.is_door: continue
            
            block1, block2 = passage.side1, passage.side2
            x1, y1 = block1.location
            x2, y2 = block2.location

            orientation = 'horizontal' if x1 == x2 else 'vertical'
            
            draw_x = (self.coord_table[(x1,y1)]['bl'][0] + self.coord_table[(x2,y2)]['br'][0]) / 2
            draw_y = (self.coord_table[(x1,y1)]['bl'][1] + self.coord_table[(x2,y2)]['tr'][1]) / 2

            status = passage.door_status
            if status == DOOR_STATUS_SECRET:
                draw_secret_door_symbol(c, draw_x, draw_y, block_size_pts, orientation)
            elif status == DOOR_STATUS_TRAPPED:
                draw_trapped_door_symbol(c, draw_x, draw_y, block_size_pts, orientation)
            elif status in [DOOR_STATUS_CLOSED, DOOR_STATUS_LOCKED]:
                draw_door_symbol(c, draw_x, draw_y, block_size_pts, orientation)

        c.setFont("Helvetica", 8)
        for i in range(self.map.MAX_X + 1):
            c.drawCentredString(self.coord_table[(i, 0)]['bl'][0] + block_size_pts/2, self.coord_table[(i,0)]['tl'][1] + 5, str(i))
        for i in range(self.map.MAX_Y + 1):
            c.drawRightString(self.coord_table[(0, i)]['bl'][0] - 5, self.coord_table[(0,i)]['bl'][1] + block_size_pts/2, str(i))

        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 8)
        all_areas = self.map.rooms + self.map.hallways
        for area in all_areas:
            center_point = get_center_of_blocks(area.blocks)
            closest_block = self._find_closest_block(center_point, area.blocks)
            draw_x = self.coord_table[closest_block.location]['bl'][0] + block_size_pts / 2
            draw_y = self.coord_table[closest_block.location]['bl'][1] + block_size_pts / 2
            c.drawCentredString(draw_x, draw_y, area.identifier.replace("Area ", ""))

        c.showPage()
        legend_end_y = self._draw_legend(c, margin, height - margin, block_size_pts)
        
        if self.include_index:
            self._draw_index(c, margin, legend_end_y - 20, height, margin)
        
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

class MarkdownGenerator:
    def __init__(self, map_instance):
        self.map = map_instance

    def save_to_markdown(self, filename):
        print(f"Saving map descriptions to {filename}...")
        with open(filename, 'w') as f:
            f.write("# Map Index\n\n")
            
            all_locations = self.map.rooms + self.map.hallways
            sorted_locations = sorted(all_locations, key=lambda x: int(''.join(filter(str.isdigit, x.identifier))))

            for loc in sorted_locations:
                wall_decos_by_direction = defaultdict(list)
                for deco in self.map.wall_decorations:
                    if deco.get_room_identifier(self.map) == loc.identifier:
                        room_center = get_center_of_blocks(loc.blocks)
                        direction_str = _get_wall_direction_string(deco.locations, room_center)
                        wall_decos_by_direction[direction_str].append(deco.description)

                if not loc.contents and not wall_decos_by_direction:
                    continue
                
                f.write(f"## {loc.identifier}\n")
                for content in loc.contents:
                    f.write(f"- {content.description}\n")
                
                for direction, descriptions in wall_decos_by_direction.items():
                    desc_str = " and ".join(descriptions)
                    f.write(f"- On the {direction} wall, you see {desc_str}.\n")
                
                f.write("\n")

        print("Markdown file saved successfully.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate a random RPG map.')
    parser.add_argument('-p', '--print', dest='pdf_filename', nargs='?', const='map.pdf', default=None,
                        help='Output the map to a PDF file. Defaults to map.pdf if no filename is provided.')
    parser.add_argument('-m', '--markdown', dest='md_filename', nargs='?', const='map.md', default=None,
                        help='Output the map descriptions to a Markdown file. Defaults to map.md if no filename is provided.')
    
    args = parser.parse_args()

    generator = Generator()
    generated_map = generator.generate()
    
    if args.pdf_filename:
        pdf_generator = PdfGenerator(generated_map, include_index=args.md_filename is None)
        pdf_generator.save_to_pdf(args.pdf_filename)

    if args.md_filename:
        md_generator = MarkdownGenerator(generated_map)
        md_generator.save_to_markdown(args.md_filename)