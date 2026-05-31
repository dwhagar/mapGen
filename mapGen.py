"""
This script handles the generation of RPG maps and their output to PDF and Markdown formats.

It uses the `reportlab` library to create PDF documents and standard file I/O for Markdown.
The script can be run from the command line and accepts various arguments to customize the
map generation and output.
"""
import argparse
from reportlab.lib import pagesizes
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, red, blue, green, white, Color, orange, brown
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
from map.passage import Passage
from map.texture import draw_door_symbol
from map.constants import OBJECT_TYPE_TRAP, ENCOUNTER_TYPE_MONSTER, PDF_BLOCK_SIZE_MM, PDF_LEGEND_VERTICAL_SPACING, PDF_LEGEND_HORIZONTAL_SPACING
from map.utils import get_center_of_blocks, get_relative_direction_from_center

def _generate_timestamped_filename(base_filename):
    """
    Generates a filename with a timestamp to prevent overwriting existing files.

    For a given base filename like 'map.pdf', this function will return a new
    filename in the format 'map-YYYYMMDD-HHMMSS.pdf'.

    :param base_filename: The original filename (e.g., 'map.pdf').
    :return: A new filename with a timestamp.
    """
    name, ext = base_filename.rsplit('.', 1)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{name}-{timestamp}.{ext}"

class PdfGenerator:
    """
    Handles the creation of a PDF document from a generated map instance.

    This class takes a map object and orchestrates the drawing of the map grid,
    walls, contents, and a legend onto a PDF canvas. It can also include a
    detailed index of the map's contents on a separate page.
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

    def _draw_legend(self, c, start_y, block_size, page_width):
        """
        Draws a legend on the PDF canvas to explain the symbols used on the map.

        The legend is centered horizontally and organized into rows to display
        the meaning of different colors and icons for map elements like floors,
        items, walls, and doors.

        :param c: The reportlab canvas object.
        :param start_y: The Y-coordinate to start drawing the legend from.
        :param block_size: The size of a single map block in points.
        :param page_width: The total width of the PDF page.
        :return: The Y-coordinate below the drawn legend.
        """
        c.setFont("Helvetica-Bold", 14)
        title_y = start_y + PDF_LEGEND_VERTICAL_SPACING
        c.drawCentredString(page_width / 2, title_y, "Map Legend")
        y_pos = start_y
        c.setFont("Helvetica", 10)

        # Define legend entries with their label, color, and a function to draw the symbol
        entries = [
            ("Floor", Color(0.8, 0.8, 0.8), lambda c, x, y, s: c.rect(x, y, s, s, fill=1)),
            ("Item", blue, lambda c, x, y, s: c.circle(x + s/2, y + s/2, s/4, fill=1)),
            ("Map Object", red, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, MapObject(object_type=OBJECT_TYPE_TRAP, block_uids=[(0,0)]).get_icon())),
            ("Encounter", green, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, Encounter(encounter_type=ENCOUNTER_TYPE_MONSTER).get_icon())),
            ("Stairs Up", orange, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, Stairs(block_uid=None, direction='up').get_icon())),
            ("Stairs Down", orange, lambda c, x, y, s: c.drawCentredString(x + s/2, y + s/4, Stairs(block_uid=None, direction='down').get_icon())),
            ("Wall", black, lambda c, x, y, s: c.rect(x, y + s*0.4, s, s*0.2, fill=1)),
        ]
        
        def draw_door_legend(c, x, y, s, color):
            c.setFillColor(color)
            draw_door_symbol(c, x + s/2, y + s/2, s, 'horizontal', color)

        # Add door types to the legend
        entries.append(("Open Door", blue, lambda c, x, y, s: draw_door_legend(c, x, y, s, blue)))
        entries.append(("Closed Door", green, lambda c, x, y, s: draw_door_legend(c, x, y, s, green)))
        entries.append(("Locked Door", brown, lambda c, x, y, s: draw_door_legend(c, x, y, s, brown)))
        entries.append(("Trapped Door", red, lambda c, x, y, s: draw_door_legend(c, x, y, s, red)))
        entries.append(("Secret Door", orange, lambda c, x, y, s: draw_door_legend(c, x, y, s, orange)))

        # Calculate layout for the legend entries
        num_entries = len(entries)
        entries_per_row = 4
        num_rows = (num_entries + entries_per_row - 1) // entries_per_row
        
        max_label_width = max(c.stringWidth(label, "Helvetica", 10) for label, _, _ in entries)
        entry_width = block_size + PDF_LEGEND_HORIZONTAL_SPACING + max_label_width + 4 * mm

        # Draw the legend entries in rows
        for row in range(num_rows):
            row_entries = entries[row*entries_per_row : (row+1)*entries_per_row]
            row_width = len(row_entries) * entry_width
            x_pos = (page_width - row_width) / 2
            
            for label, color, shape_func in row_entries:
                c.setFillColor(color)
                shape_func(c, x_pos, y_pos, block_size)
                c.setFillColor(black)
                c.drawString(x_pos + block_size + PDF_LEGEND_HORIZONTAL_SPACING, y_pos + (block_size/4), label)
                x_pos += entry_width
            
            y_pos -= PDF_LEGEND_VERTICAL_SPACING * 1.5
        
        return y_pos

    def _build_coordinate_translation_table(self, pagesize, margin, block_size_pts):
        """
        Builds a lookup table to translate map grid coordinates to PDF coordinates.

        This is necessary because the map uses a grid system (e.g., 1,1 to 25,25),
        while the PDF uses a point-based system. This method pre-calculates the
        PDF coordinates for the corners of each grid block.

        :param pagesize: A tuple (width, height) of the PDF page in points.
        :param margin: The margin around the map on the PDF page.
        :param block_size_pts: The size of a single map block in points.
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
        Prepares a list of styled items for the PDF index for a given location.

        :param loc: The location object (room or hallway).
        :param style_body: The reportlab style for the list item text.
        :return: A list of `ListItem` objects.
        """
        items = []
        for content in loc.contents:
            items.append(ListItem(Paragraph(content.description, style_body), leftIndent=35))
        
        # Group wall decorations by direction
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
        Draws the map index on a new page of the PDF.

        The index lists each room and hallway and their contents.

        :param c: The reportlab canvas object.
        :param start_x: The X-coordinate to start drawing from.
        :param start_y: The Y-coordinate to start drawing from.
        :param page_height: The height of the PDF page.
        :param margin: The margin of the PDF page.
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
            
            # If no items, provide a default description
            if not list_items:
                list_items.append(ListItem(Paragraph("This area appears to be empty.", style_body), leftIndent=35))

            # Draw location identifier
            p = Paragraph(f"{loc.identifier}:", style_heading)
            p_w, p_h = p.wrapOn(c, 500, 50)
            if y_pos - p_h < margin: # Check for page break
                c.showPage()
                y_pos = page_height - margin
            p.drawOn(c, start_x, y_pos - p_h)
            y_pos -= p_h

            # Draw list of contents
            list_flowable = ListFlowable(list_items, bulletType='bullet', start='bulletchar')
            list_flowable.wrapOn(c, 480, 1000)
            list_h = list_flowable.height
            
            if y_pos - list_h < margin: # Check for page break
                c.showPage()
                y_pos = page_height - margin

            list_flowable.drawOn(c, start_x + 20, y_pos - list_h)
            y_pos -= list_h + 10

    def _find_closest_block(self, center, blocks):
        """
        Finds the block in a list that is closest to a given center point.

        This is used to determine the best block to place area identifiers in.

        :param center: A tuple (x, y) representing the center point.
        :param blocks: A list of block objects.
        :return: The block object closest to the center.
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
        Generates and saves the complete map to a PDF file.

        This method orchestrates the entire PDF generation process, from setting up
        the canvas to drawing the map elements and saving the file.

        :param filename: The name of the file to save the PDF to.
        :param pagesize_str: The desired page size (e.g., 'A4', 'Letter').
        """
        print(f"Saving map to {filename}...")
        pagesize = getattr(pagesizes, pagesize_str.upper(), pagesizes.A4)
        c = canvas.Canvas(filename, pagesize=pagesize)
        width, height = pagesize
        block_size_pts = PDF_BLOCK_SIZE_MM * mm
        margin = 20 * mm

        self._build_coordinate_translation_table((width, height), margin, block_size_pts)

        # 1. Draw block backgrounds (floors)
        for (x, y), block in self.map.blocks.items():
            if block.empty:
                continue
            draw_x, draw_y = self.coord_table[(x, y)]['bl']
            
            container = self.map.get_area_by_uid(block.area_uid)
            c.setFillColor(container.color if container and container.color else Color(0.8, 0.8, 0.8))
            c.rect(draw_x, draw_y, block_size_pts, block_size_pts, fill=1, stroke=0)

        # 2. Draw grid lines
        c.setStrokeColor(black)
        c.setLineWidth(0.1)
        grid_x_start, grid_y_start = self.coord_table[(1,1)]['tl']
        grid_end_x = self.coord_table[(self.map.width, 1)]['tr'][0]
        grid_end_y = self.coord_table[(1, self.map.height)]['bl'][1]
        for i in range(self.map.width + 1):
            c.line(grid_x_start + i * block_size_pts, grid_y_start, grid_x_start + i * block_size_pts, grid_end_y)
        for i in range(self.map.height + 1):
            c.line(grid_x_start, grid_y_start - i * block_size_pts, grid_end_x, grid_y_start - i * block_size_pts)

        # 3. Draw walls
        c.setStrokeColor(black)
        c.setLineWidth(3)
        c.setLineCap(1) # Square line caps
        for block in self.map.blocks.values():
            if block.empty:
                continue
            corners = self.coord_table[(block.location.x, block.location.y)]
            
            # A wall is drawn if the side is a Wall or a Passage that is a door
            if isinstance(block.north, Wall) or (isinstance(block.north, Passage) and block.north.is_door):
                c.line(corners['tl'][0], corners['tl'][1], corners['tr'][0], corners['tr'][1])
            if isinstance(block.south, Wall) or (isinstance(block.south, Passage) and block.south.is_door):
                c.line(corners['bl'][0], corners['bl'][1], corners['br'][0], corners['br'][1])
            if isinstance(block.east, Wall) or (isinstance(block.east, Passage) and block.east.is_door):
                c.line(corners['br'][0], corners['br'][1], corners['tr'][0], corners['tr'][1])
            if isinstance(block.west, Wall) or (isinstance(block.west, Passage) and block.west.is_door):
                c.line(corners['bl'][0], corners['bl'][1], corners['tl'][0], corners['tl'][1])

        # 4. Draw block contents (items, stairs, etc.)
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

        # 5. Draw door symbols
        for passage in self.map.passages:
            if not passage.is_door: continue
            
            # Determine door color based on its state
            door_color = green  # Default: closed
            if passage.is_secret: door_color = orange
            elif passage.is_trapped: door_color = red
            elif passage.is_locked: door_color = brown
            elif passage.is_open: door_color = blue

            block1, block2 = passage.side1, passage.side2
            x1, y1 = block1.location.x, block1.location.y
            x2, y2 = block2.location.x, block2.location.y
            
            # Calculate midpoint between the two blocks for the door symbol
            draw_x = (self.coord_table[(x1,y1)]['bl'][0] + self.coord_table[(x2,y2)]['br'][0]) / 2
            draw_y = (self.coord_table[(x1,y1)]['bl'][1] + self.coord_table[(x2,y2)]['tr'][1]) / 2

            draw_door_symbol(c, draw_x, draw_y, block_size_pts, passage.orientation, door_color)

        # 6. Draw coordinates and area identifiers
        c.setFont("Helvetica", 8)
        for i in range(1, self.map.width + 1): # X-axis coordinates
            c.drawCentredString(self.coord_table[(i, 1)]['bl'][0] + block_size_pts/2, self.coord_table[(i,1)]['tl'][1] + 5, str(i))
        for i in range(1, self.map.height + 1): # Y-axis coordinates
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

        # Draw the legend at the bottom of the map
        legend_y_start = grid_end_y - 20 * mm
        self._draw_legend(c, legend_y_start, block_size_pts, width)
        
        # If requested, draw the index on a new page
        if self.include_index:
            c.showPage()
            self._draw_index(c, margin, height - margin, height, margin)

        c.save()
        print("PDF saved successfully.")

class MarkdownGenerator:
    """
    Generates a Markdown file describing the contents of the map.
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

        The file will contain a list of all locations (rooms and hallways)
        and a description of their contents.

        :param filename: The name of the file to save the Markdown to.
        """
        print(f"Saving map descriptions to {filename}...")
        with open(filename, 'w') as f:
            f.write("# Map Index\n\n")
            
            all_locations = self.map.rooms + self.map.hallways
            sorted_locations = sorted(all_locations, key=lambda x: int(''.join(filter(str.isdigit, x.identifier))))

            for loc in sorted_locations:
                f.write(f"## {loc.identifier}\n")
                
                # Gather descriptions of contents and wall decorations
                contents_descriptions = [f"- {content.description}" for content in loc.contents]
                
                wall_decos_by_direction = defaultdict(list)
                for deco in self.map.wall_decorations:
                    if deco.area_uid == loc.unique_id:
                        room_center = get_center_of_blocks(loc.blocks)
                        direction_str = get_relative_direction_from_center(deco.locations, room_center)
                        wall_decos_by_direction[direction_str].append(deco.description)

                for direction, descriptions in wall_decos_by_direction.items():
                    desc_str = " and ".join(descriptions)
                    contents_descriptions.append(f"- On the {direction} wall, you see {desc_str}.")
                
                # Write descriptions or a default message
                if contents_descriptions:
                    f.write("\n".join(contents_descriptions))
                    f.write("\n")
                else:
                    f.write("- This area appears to be empty.\n")
                
                f.write("\n")

        print("Markdown file saved successfully.")

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Generate a random RPG map.')
    parser.add_argument('-p', '--print', dest='pdf_filename', nargs='?', const='map.pdf', default=None,
                        help='Output the map to a PDF file. Defaults to map.pdf if no filename is provided.')
    parser.add_argument('--pagesize', dest='pagesize', type=str, default='A4',
                        help='Set the page size of the PDF output. Defaults to A4.')
    parser.add_argument('-m', '--markdown', dest='md_filename', nargs='?', const='map.md', default=None,
                        help='Output the map descriptions to a Markdown file. Defaults to map.md if no filename is provided.')
    parser.add_argument('--add-object', dest='add_objects', action='append',
                        help='Add an object to the map. Format: INT or INT,x,y. Can be used multiple times.')
    parser.add_argument('-W', '--width', dest='width', type=int, default=25,
                        help='Set the width of the map.')
    parser.add_argument('-H', '--height', type=int, default=25,
                        help='Set the height of the map.')
    
    args = parser.parse_args()

    # Process --add-object arguments
    add_object_data = []
    if args.add_objects:
        for obj_str in args.add_objects:
            try:
                parts = list(map(int, obj_str.split(',')))
                if len(parts) == 1:
                    add_object_data.append((parts[0], None, None)) # ID only
                elif len(parts) == 3:
                    add_object_data.append(tuple(parts)) # ID, x, y
                else:
                    raise ValueError
            except ValueError:
                print(f"Invalid format for --add-object: '{obj_str}'. Please use INT or INT,x,y.")
                exit(1)

    # Generate the map
    generator = Generator(width=args.width, height=args.height, add_objects=add_object_data)
    generated_map = generator.generate()
    
    # Output to PDF if requested
    if args.pdf_filename:
        filename = args.pdf_filename
        # Use a timestamped filename if the default 'map.pdf' is used
        if filename == 'map.pdf':
            filename = _generate_timestamped_filename(filename)
        pdf_generator = PdfGenerator(generated_map, include_index=args.md_filename is None)
        pdf_generator.save_to_pdf(filename, args.pagesize)

    # Output to Markdown if requested
    if args.md_filename:
        md_generator = MarkdownGenerator(generated_map)
        md_generator.save_to_markdown(args.md_filename)
