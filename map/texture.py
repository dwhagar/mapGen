from reportlab.lib.colors import dimgrey, black, green, blue, red

def draw_dots(canvas, x, y, size):
    dot_radius = size * 0.05
    for i in range(3):
        for j in range(3):
            dot_x = x + (i + 0.5) * (size / 3)
            dot_y = y + (j + 0.5) * (size / 3)
            canvas.circle(dot_x, dot_y, dot_radius, fill=1, stroke=0)

def draw_lines(canvas, x, y, size):
    canvas.setStrokeColor(dimgrey)
    canvas.setLineWidth(0.5)
    for i in range(-1, 2):
        canvas.line(x, y + i * size / 2, x + size, y + size + i * size / 2)

def draw_crosshatch(canvas, x, y, size):
    canvas.setStrokeColor(dimgrey)
    canvas.setLineWidth(0.5)
    for i in range(-2, 3):
        canvas.line(x, y + i * size / 2, x + size, y + size + i * size / 2)
    for i in range(-2, 3):
        canvas.line(x, y - i * size / 2, x + size, y - size - i * size / 2)

TEXTURES = {
    "dots": draw_dots,
    "lines": draw_lines,
    "crosshatch": draw_crosshatch,
}

def draw_door_symbol(canvas, x, y, size, orientation, color=green):
    """Draws a door symbol of a given color centered on the coordinates."""
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
    """Draws a secret door symbol (blue)."""
    draw_door_symbol(canvas, x, y, size, orientation, color=blue)

def draw_trapped_door_symbol(canvas, x, y, size, orientation):
    """Draws a trapped door symbol (red)."""
    draw_door_symbol(canvas, x, y, size, orientation, color=red)
