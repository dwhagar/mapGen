"""
This module contains functions for drawing various graphical elements on the PDF canvas,
such as textures and door symbols. These functions are used by the PdfGenerator to
create a visual representation of the map.
"""
from reportlab.lib.colors import dimgrey, black, green, blue, red

def draw_dots(canvas, x, y, size):
    """
    Draws a dot pattern within a specified area.

    :param canvas: The reportlab canvas object.
    :param x: The starting x-coordinate of the area.
    :param y: The starting y-coordinate of the area.
    :param size: The size of the square area to fill with dots.
    """
    dot_radius = size * 0.05
    for i in range(3):
        for j in range(3):
            dot_x = x + (i + 0.5) * (size / 3)
            dot_y = y + (j + 0.5) * (size / 3)
            canvas.circle(dot_x, dot_y, dot_radius, fill=1, stroke=0)

def draw_lines(canvas, x, y, size):
    """
    Draws a diagonal line pattern within a specified area.

    :param canvas: The reportlab canvas object.
    :param x: The starting x-coordinate of the area.
    :param y: The starting y-coordinate of the area.
    :param size: The size of the square area to fill with lines.
    """
    canvas.setStrokeColor(dimgrey)
    canvas.setLineWidth(0.5)
    for i in range(-1, 2):
        canvas.line(x, y + i * size / 2, x + size, y + size + i * size / 2)

def draw_crosshatch(canvas, x, y, size):
    """
    Draws a crosshatch pattern within a specified area.

    :param canvas: The reportlab canvas object.
    :param x: The starting x-coordinate of the area.
    :param y: The starting y-coordinate of the area.
    :param size: The size of the square area to fill with crosshatching.
    """
    canvas.setStrokeColor(dimgrey)
    canvas.setLineWidth(0.5)
    for i in range(-2, 3):
        canvas.line(x, y + i * size / 2, x + size, y + size + i * size / 2)
    for i in range(-2, 3):
        canvas.line(x, y - i * size / 2, x + size, y - size - i * size / 2)

# A dictionary mapping texture names to their drawing functions.
# This allows for easily extending the available textures.
TEXTURES = {
    "dots": draw_dots,
    "lines": draw_lines,
    "crosshatch": draw_crosshatch,
}

def draw_door_symbol(canvas, x, y, size, orientation, color=green):
    """
    Draws a generic door symbol centered on the given coordinates.

    The symbol is a colored rectangle, oriented either horizontally or vertically.

    :param canvas: The reportlab canvas object.
    :param x: The center x-coordinate for the door symbol.
    :param y: The center y-coordinate for the door symbol.
    :param size: The size of the block, used to scale the door symbol.
    :param orientation: 'horizontal' or 'vertical'.
    :param color: The reportlab color object for the door. Defaults to green.
    """
    door_thickness = size * 0.25
    door_length = size * 0.7
    canvas.setFillColor(color)

    if orientation == 'horizontal':
        rect_x = x - (door_length / 2)
        rect_y = y - (door_thickness / 2)
        canvas.rect(rect_x, rect_y, door_length, door_thickness, fill=1, stroke=0)
    else:  # vertical
        rect_x = x - (door_thickness / 2)
        rect_y = y - (door_length / 2)
        canvas.rect(rect_x, rect_y, door_thickness, door_length, fill=1, stroke=0)

def draw_secret_door_symbol(canvas, x, y, size, orientation):
    """
    Draws a secret door symbol, which is a blue door symbol.

    :param canvas: The reportlab canvas object.
    :param x: The center x-coordinate for the door symbol.
    :param y: The center y-coordinate for the door symbol.
    :param size: The size of the block, used to scale the door symbol.
    :param orientation: 'horizontal' or 'vertical'.
    """
    draw_door_symbol(canvas, x, y, size, orientation, color=blue)

def draw_trapped_door_symbol(canvas, x, y, size, orientation):
    """
    Draws a trapped door symbol, which is a red door symbol.

    :param canvas: The reportlab canvas object.
    :param x: The center x-coordinate for the door symbol.
    :param y: The center y-coordinate for the door symbol.
    :param size: The size of the block, used to scale the door symbol.
    :param orientation: 'horizontal' or 'vertical'.
    """
    draw_door_symbol(canvas, x, y, size, orientation, color=red)
