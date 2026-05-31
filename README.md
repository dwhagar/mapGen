# RPG Map Generator

This project is a Python script for procedurally generating random maps suitable for tabletop role-playing games. It creates complex layouts with rooms and hallways, and can place various objects within them. The generated map can be saved as a PDF, which includes a visual representation of the map with a legend, and optionally an index of all map contents. Alternatively, a Markdown file can be generated, detailing the contents of each area.

## Features

*   Procedural generation of rooms and hallways.
*   Customizable map dimensions (width and height).
*   Placement of items, objects, encounters, and stairs.
*   PDF export of the visual map, including a legend.
*   Optional, detailed index of map contents in either PDF or Markdown format.
*   Timestamped filenames for PDF outputs to avoid overwriting previous maps.
*   Support for various page sizes for PDF output (e.g., A4, Letter).
*   Ability to add specific objects at random or specified locations via command-line arguments.

## Usage

To use the map generator, run the `mapGen.py` script from the command line with the desired options.

### Command-Line Arguments

*   `-p, --print [filename]`: Outputs the map to a PDF file. If no filename is provided, it defaults to `map-<timestamp>.pdf`.
*   `--pagesize <size>`: Sets the page size for the PDF output. Common values are `A4` or `Letter`. Defaults to `A4`.
*   `-m, --markdown [filename]`: Outputs the map descriptions to a Markdown file. If no filename is provided, it defaults to `map.md`.
*   `--add-object <INT | INT,x,y>`: Adds an object to the map. This argument can be used multiple times. The object is identified by an integer ID. You can optionally specify the x and y coordinates for its location.
*   `-W, --width <width>`: Sets the width of the map in grid blocks. Defaults to 25.
*   `-H, --height <height>`: Sets the height of the map in grid blocks. Defaults to 25.

### Examples

**Generate a default map and save it to a timestamped PDF:**

```bash
python mapGen.py --print
```

**Generate a 50x50 map and save it to `mymap.pdf` and `mymap.md`:**

```bash
python mapGen.py --width 50 --height 50 --print mymap.pdf --markdown mymap.md
```

**Generate a map on 'Letter' size paper and add an object:**

```bash
python mapGen.py --pagesize Letter --print --add-object 1
```

## Dependencies

This project requires the `reportlab` library for PDF generation. You can install it using pip:

```bash
pip install reportlab
```
