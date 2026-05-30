import argparse
from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, red, blue, green, white, Color, orange
from reportlab.lib.units import mm
import math
from collections import defaultdict
from reportlab.platypus import Paragraph, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

from map.generator import Generator
from map.item import Item
from map.object import MapObject
from map.encounter import Encounter
from map.stairs import Stairs
from map.wall import Wall
from map.texture import draw_door_symbol
from map.constants import OBJECT_TYPE_TRAP, ENCOUNTER_TYPE_MONSTER, PDF_BLOCK_SIZE_MM, PDF_LEGEND_VERTICAL_SPACING, PDF_LEGEND_HORIZONTAL_SPACING
from map.utils import get_center_of_blocks, get_relative_direction_from_center

def _generate_timestamped_filename(base_filename):
    """
    Generates a timestamped filename.
    """
    name, ext = base_filename.rsplit('.', 1)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{name}-{timestamp}.{ext}"

class PdfGenerator:
    """
    Generates a PDF of the map.
    """
    def __init__(self, map_instance, include_index=True):
        """
        Initializes the PdfGenerator.

        :param map_instance: The map instance to generate the PDF from.
        :param include_index: Whether to include an index of the map's contents.
        """
        self.map = map_instance
        self.coord_table = {}
        self.include_index = include_index

    def _draw_legend(self, c, start_x, start_y, block_size):
        """
        Draws the legend on the PDF.
        """
        c.setFont("Helvetica-Bold", 14)
        c.drawString(start_x, start_y, "Map Legend")
        y_pos = start_y - PDF_LEGEND_VERTICAL_SPACING
        c.setFont("Helvetica", 10)

        def draw_entry(label, color, shape_func):
            nonlocal y_pos
            c.setFillColor(color)
            shape_func(c, start_x, y_pos, block_size)
            c.setFillColor(black)
            c.drawString(start_x + block_size + PDF_LEGEND_HORIZONTAL_SPACING, y_pos + (block_size/4), label)
            y_pos -= PDF_LEGEND_VERTICAL_SPACING

        draw_entry("Floor", Color(0.8, 0.8, 0.8), lambda c, x, y, s: c.rect(x, y, s, s, fill=1))
        draw_entry("Item", blue, lambda c, x, y, s: c.circle(x + s/2, y + s/2, s/4, fill=1))
        draw_entry("Map Object", red, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, MapObject(object_type=OBJECT_TYPE_TRAP, block_uids=[(0,0)]).get_icon()))
        draw_entry("Encounter", green, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, Encounter(encounter_type=ENCOUNTER_TYPE_MONSTER).get_icon()))
        draw_entry("Stairs Up", orange, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, Stairs(block_uid=None, direction='up').get_icon()))
        draw_entry("Stairs Down", orange, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, Stairs(block_uid=None, direction='down').get_icon()))
        draw_entry("Wall", black, lambda c, x, y, s: c.rect(x, y + s*0.4, s, s*0.2, fill=1))
        
        def draw_door_legend(c, x, y, s):
            c.setFillColor(black)
            c.rect(x, y + s*0.4, s, s*0.2, fill=1)
            draw_door_symbol(c, x + s/2, y + s/2, s, 'horizontal')
        draw_entry("Door", green, draw_door_legend)
        
        return y_pos

    def _build_coordinate_translation_table(self, pagesize, margin, block_size_pts):
        """
        Builds a table to translate map coordinates to PDF coordinates.
        """
        width, height = pagesize
        map_width_pts = (self.map.width + 1) * block_size_pts
        map_height_pts = (self.map.height + 1) * block_size_pts
        x_offset = margin
        y_offset = height - margin - map_height_pts

        for y_grid in range(1, self.map.height + 1):
            for x_grid in range(1, self.map.width + 1):
                bl_x = x_offset + (x_grid - 1) * block_size_pts
                bl_y = y_offset + (self.map.height - y_grid) * block_size_pts
                self.coord_table[(x_grid, y_grid)] = {
                    'bl': (bl_x, bl_y),
                    'br': (bl_x + block_size_pts, bl_y),
                    'tl': (bl_x, bl_y + block_size_pts),
                    'tr': (bl_x + block_size_pts, bl_y + block_size_pts)
                }

    def _prepare_list_items(self, loc, style_body):
        """
        Prepares a list of items for the index.
        """
        items = []
        for content in loc.contents:
            items.append(ListItem(Paragraph(content.description, style_body), leftIndent=35))
        
        wall_decos_by_direction = defaultdict(list)
        for deco in self.map.wall_decorations:
            if deco.area_uid == loc.unique_id:
                room_center = get_center_of_blocks(loc.blocks)
                direction_str = get_relative_direction_from_center(deco.locations, room_center)
                wall_decos_by_direction[direction_str].append(deco.description)

        for direction, descriptions in wall_decos_by_direction.items():
            desc_str = " and ".join(descriptions)
            items.append(ListItem(Paragraph(f"On the {direction} wall, you see {desc_str}.", style_body), leftIndent=35))
            
        return items

    def _draw_index(self, c, start_x, start_y, page_height, margin):
        """
        Draws the index on the PDF.
        """
        styles = getSampleStyleSheet()
        style_body = styles['BodyText']
        style_heading = styles['h2']
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(start_x, start_y, "Map Index")
        
        y_pos = start_y - PDF_LEGEND_VERTICAL_SPACING
        
        all_locations = self.map.rooms + self.map.hallways
        sorted_locations = sorted(all_locations, key=lambda x: int(''.join(filter(str.isdigit, x.identifier))))

        for loc in sorted_locations:
            list_items = self._prepare_list_items(loc, style_body)
            
            # If no specific items or wall decorations, add a default description
            if not list_items:
                list_items.append(ListItem(Paragraph("This area appears to be empty.", style_body), leftIndent=35))

            p = Paragraph(f"{loc.identifier}:", style_heading)
            p_w, p_h = p.wrapOn(c, 500, 50)
            if y_pos - p_h < margin:
                c.showPage()
                y_pos = page_height - margin
            p.drawOn(c, start_x, y_pos - p_h)
            y_pos -= p_h

            list_flowable = ListFlowable(list_items, bulletType='bullet', start='bulletchar')
            list_flowable.wrapOn(c, 480, 1000) # Arbitrarily large height
            list_h = list_flowable.height
            
            if y_pos - list_h < margin:
                c.showPage()
                y_pos = page_height - margin

            list_flowable.drawOn(c, start_x + 20, y_pos - list_h)
            y_pos -= list_h + 10

    def _find_closest_block(self, center, blocks):
        """
        Finds the closest block to a given center point.
        """
        closest_block = None
        min_dist = float('inf')
        for block in blocks:
            dist = math.sqrt((center[0] - block.location.x)**2 + (center[1] - block.location.y)**2)
            if dist < min_dist:
                min_dist = dist
                closest_block = block
        return closest_block

    def save_to_pdf(self, filename, pagesize_str='A4'):
        """
        Saves the map to a PDF file.
        """
        print(f"Saving map to {filename}...")
        pagesize = getattr(pagesizes, pagesize_str.upper(), pagesizes.A4)
        c = canvas.Canvas(filename, pagesize=pagesize)
        width, height = pagesize
        block_size_pts = PDF_BLOCK_SIZE_MM * mm
        margin = 20 * mm

        self._build_coordinate_translation_table((width, height), margin, block_size_pts)

        for (x, y), block in self.map.blocks.items():
            if block.empty:
                continue
            draw_x, draw_y = self.coord_table[(x, y)]['bl']
            
            container = self.map.get_area_by_uid(block.area_uid)
            if container and container.color:
                c.setFillColor(container.color)
            else:
                c.setFillColor(Color(0.8, 0.8, 0.8))
            c.rect(draw_x, draw_y, block_size_pts, block_size_pts, fill=1, stroke=0)

        for (x, y), block in self.map.blocks.items():
            if block.empty:
                continue
            draw_x, draw_y = self.coord_table[(x, y)]['bl']
            for content in block.contents:
                if isinstance(content, Stairs):
                    c.setFillColor(orange)
                    c.drawCentredString(draw_x + block_size_pts/2, draw_y + block_size_pts/4, content.get_icon())
                elif isinstance(content, Encounter):
                    c.setFillColor(green)
                    c.drawCentredString(draw_x + block_size_pts/2, draw_y + block_size_pts/4, content.get_icon())
                elif isinstance(content, MapObject):
                    c.setFillColor(red)
                    c.drawCentredString(draw_x + block_size_pts/2, draw_y + block_size_pts/4, content.get_icon())
                elif isinstance(content, Item):
                    c.setFillColor(blue)
                    c.circle(draw_x + block_size_pts / 2, draw_y + block_size_pts / 2, block_size_pts / 4, fill=1, stroke=0)

        c.setStrokeColor(black)
        c.setLineWidth(0.1)
        grid_x_start, grid_y_start = self.coord_table[(1,1)]['tl']
        grid_end_x = self.coord_table[(self.map.width, 1)]['tr'][0]
        grid_end_y = self.coord_table[(1, self.map.height)]['bl'][1]
        for i in range(self.map.width + 1):
            c.line(grid_x_start + i * block_size_pts, grid_y_start, grid_x_start + i * block_size_pts, grid_end_y)
        for i in range(self.map.height + 1):
            c.line(grid_x_start, grid_y_start - i * block_size_pts, grid_end_x, grid_y_start - i * block_size_pts)

        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.setLineCap(1)
        for block in self.map.blocks.values():
            if block.empty:
                continue
            corners = self.coord_table[(block.location.x, block.location.y)]
            
            if isinstance(block.north, Wall): c.line(corners['tl'][0], corners['tl'][1], corners['tr'][0], corners['tr'][1])
            if isinstance(block.south, Wall): c.line(corners['bl'][0], corners['bl'][1], corners['br'][0], corners['br'][1])
            if isinstance(block.east, Wall): c.line(corners['br'][0], corners['br'][1], corners['tr'][0], corners['tr'][1])
            if isinstance(block.west, Wall): c.line(corners['bl'][0], corners['bl'][1], corners['tl'][0], corners['tl'][1])

        for passage in self.map.passages:
            if not passage.is_door: continue
            
            block1, block2 = passage.side1, passage.side2
            x1, y1 = block1.location.x, block1.location.y
            x2, y2 = block2.location.x, block2.location.y

            orientation = 'horizontal' if x1 == x2 else 'vertical'
            
            draw_x = (self.coord_table[(x1,y1)]['bl'][0] + self.coord_table[(x2,y2)]['br'][0]) / 2
            draw_y = (self.coord_table[(x1,y1)]['bl'][1] + self.coord_table[(x2,y2)]['tr'][1]) / 2

            draw_door_symbol(c, draw_x, draw_y, block_size_pts, orientation)

        c.setFont("Helvetica", 8)
        for i in range(1, self.map.width + 1):
            c.drawCentredString(self.coord_table[(i, 1)]['bl'][0] + block_size_pts/2, self.coord_table[(i,1)]['tl'][1] + 5, str(i))
        for i in range(1, self.map.height + 1):
            c.drawRightString(self.coord_table[(1, i)]['bl'][0] - 5, self.coord_table[(1,i)]['bl'][1] + block_size_pts/2, str(i))

        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 8)
        all_areas = self.map.rooms + self.map.hallways
        for area in all_areas:
            center_point = get_center_of_blocks(area.blocks)
            closest_block = self._find_closest_block(center_point, area.blocks)
            draw_x = self.coord_table[(closest_block.location.x, closest_block.location.y)]['bl'][0] + block_size_pts / 2
            draw_y = self.coord_table[(closest_block.location.x, closest_block.location.y)]['bl'][1] + block_size_pts / 2
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
    """
    Generates a Markdown file of the map's contents.
    """
    def __init__(self, map_instance):
        """
        Initializes the MarkdownGenerator.

        :param map_instance: The map instance to generate the Markdown file from.
        """
        self.map = map_instance

    def save_to_markdown(self, filename):
        """
        Saves the map's contents to a Markdown file.
        """
        print(f"Saving map descriptions to {filename}...")
        with open(filename, 'w') as f:
            f.write("# Map Index\n\n")
            
            all_locations = self.map.rooms + self.map.hallways
            sorted_locations = sorted(all_locations, key=lambda x: int(''.join(filter(str.isdigit, x.identifier))))

            for loc in sorted_locations:
                wall_decos_by_direction = defaultdict(list)
                for deco in self.map.wall_decorations:
                    if deco.area_uid == loc.unique_id:
                        room_center = get_center_of_blocks(loc.blocks)
                        direction_str = get_relative_direction_from_center(deco.locations, room_center)
                        wall_decos_by_direction[direction_str].append(deco.description)

                f.write(f"## {loc.identifier}\n")
                
                # If no specific items or wall decorations, add a default description
                if not loc.contents and not wall_decos_by_direction:
                    f.write(f"- This area appears to be empty.\n")
                else:
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
    parser.add_argument('--pagesize', dest='pagesize', type=str, default='A4',
                        help='Set the page size of the PDF output. Defaults to A4.')
    parser.add_argument('-m', '--markdown', dest='md_filename', nargs='?', const='map.md', default=None,
                        help='Output the map descriptions to a Markdown file. Defaults to map.md if no filename is provided.')
    parser.add_argument('--add-object', dest='add_object',
                        help='Add an object to the map at a specific location. Format: index,x,y')
    parser.add_argument('-W', '--width', dest='width', type=int, default=25,
                        help='Set the width of the map.')
    parser.add_argument('-H', '--height', type=int, default=25,
                        help='Set the height of the map.')
    
    args = parser.parse_args()

    add_object_data = None
    if args.add_object:
        try:
            index, x, y = map(int, args.add_object.split(','))
            add_object_data = (index, x, y)
        except ValueError:
            print("Invalid format for --add-object. Please use index,x,y.")
            exit(1)

    generator = Generator(width=args.width, height=args.height, add_object=add_object_data)
    generated_map = generator.generate()
    
    if args.pdf_filename:
        filename = args.pdf_filename
        if filename == 'map.pdf':
            filename = _generate_timestamped_filename(filename)
        pdf_generator = PdfGenerator(generated_map, include_index=args.md_filename is None)
        pdf_generator.save_to_pdf(filename, args.pagesize)

    if args.md_filename:
        md_generator = MarkdownGenerator(generated_map)
        md_generator.save_to_markdown(args.md_filename)