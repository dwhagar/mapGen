"""
This module contains the functions for generating a maze layout for the map.
"""
import random
from .hallway import Hallway
from .passage import Passage
from .block import Block

def generate_maze_layout(the_map, hallway_count):
    """
    Carves a maze into all empty blocks of the map, creating distinct hallways for each segment and
    connecting them with passages at turns. It also connects rooms to the maze.

    :param the_map: The Map object to modify.
    :param hallway_count: The current count of hallways, used for naming.
    :return: The updated hallway count.
    """
    hallway_count = _carve_maze(the_map, hallway_count)
    _merge_short_hallways(the_map)
    _connect_rooms_to_maze(the_map)
    return hallway_count

def _carve_maze(the_map, hallway_count):
    """
    Carves a maze into the empty blocks of the map using a recursive backtracking algorithm.
    This method creates new Hallway objects for each segment of the maze and connects them
    with Passage objects where the maze turns.
    """
    print("Carving maze with passages...")

    # A dictionary to keep track of which hallway each block belongs to and its direction.
    block_info = {}

    # Iterate over the map grid, starting a new maze carving from any unvisited empty block.
    for y in range(1, the_map.height + 1, 2):
        for x in range(1, the_map.width + 1, 2):
            start_block = the_map.get_block_at(x, y)
            if start_block and start_block.empty:
                # Start of a new maze section.
                stack = [(x, y)]
                
                hallway_count += 1
                current_hallway = Hallway(identifier=f"H{hallway_count}")
                the_map.add_hallway(current_hallway)
                
                # The initial direction is neutral.
                current_direction = (0, 0)

                # Mark the starting block as part of the new hallway.
                start_block.area_uid = current_hallway.unique_id
                start_block.empty = False
                current_hallway.blocks.append(start_block)
                block_info[(x, y)] = {'hallway': current_hallway, 'direction': current_direction}

                while stack:
                    cx, cy = stack[-1]
                    current_block = the_map.get_block_at(cx, cy)
                    
                    info = block_info.get((cx, cy))
                    if not info:
                        stack.pop()
                        continue
                    
                    current_hallway = info['hallway']
                    current_direction = info['direction']

                    # Find unvisited neighbors.
                    neighbors = []
                    for dx, dy in [(0, -2), (0, 2), (2, 0), (-2, 0)]:
                        nx, ny = cx + dx, cy + dy
                        if 1 <= nx <= the_map.width and 1 <= ny <= the_map.height:
                            neighbor_block = the_map.get_block_at(nx, ny)
                            if neighbor_block and neighbor_block.empty:
                                neighbors.append((nx, ny, (cx + dx // 2, cy + dy // 2), (dx // 2, dy // 2)))

                    if neighbors:
                        nx, ny, (px, py), new_direction = random.choice(neighbors)
                        
                        path_block = the_map.get_block_at(px, py)
                        neighbor_block = the_map.get_block_at(nx, ny)

                        # If the direction changes, create a new hallway and a passage.
                        if new_direction != current_direction and current_direction != (0, 0):
                            hallway_count += 1
                            next_hallway = Hallway(identifier=f"H{hallway_count}")
                            the_map.add_hallway(next_hallway)
                            
                            passage_direction = _get_direction_from_move(current_block, path_block)
                            Passage.create(the_map, current_block, path_block, passage_direction, is_door=False, is_open=True)
                            
                            current_hallway = next_hallway
                        
                        # Assign the path and neighbor blocks to the current hallway.
                        path_block.area_uid = current_hallway.unique_id
                        path_block.empty = False
                        current_hallway.blocks.append(path_block)
                        block_info[(px, py)] = {'hallway': current_hallway, 'direction': new_direction}

                        neighbor_block.area_uid = current_hallway.unique_id
                        neighbor_block.empty = False
                        current_hallway.blocks.append(neighbor_block)
                        block_info[(nx, ny)] = {'hallway': current_hallway, 'direction': new_direction}
                        
                        stack.append((nx, ny))
                    else:
                        # No unvisited neighbors, backtrack.
                        stack.pop()

    # After carving, set the walls for all maze blocks.
    all_maze_blocks = [block for h in the_map.hallways for block in h.blocks if h.identifier.startswith('H')]
    for block in all_maze_blocks:
        block._set_initial_walls(the_map)
        
    print("Maze carving complete.")
    return hallway_count

def _merge_short_hallways(the_map, min_length=3):
    """
    Merges maze hallways that are shorter than a minimum length into their neighbors.
    This helps to clean up the maze by removing tiny, insignificant hallway segments.
    """
    print("Merging short hallways...")
    while True:
        # Find all short hallways that are part of the maze.
        short_hallways = [h for h in the_map.hallways if h.identifier.startswith('H') and len(h.blocks) < min_length]
        
        if not short_hallways:
            break

        made_a_merge = False
        for short_h in short_hallways:
            # Find a passage connecting this short hallway to another maze hallway.
            for passage in the_map.passages:
                neighbor_uid = None
                if passage.side1.area_uid == short_h.unique_id:
                    neighbor_uid = passage.side2.area_uid
                elif passage.side2.area_uid == short_h.unique_id:
                    neighbor_uid = passage.side1.area_uid

                if neighbor_uid:
                    neighbor_hallway = the_map.get_area_by_uid(neighbor_uid)
                    if isinstance(neighbor_hallway, Hallway) and neighbor_hallway.identifier.startswith('H'):
                        # Merge the short hallway into its neighbor.
                        print(f"Merging hallway {short_h.identifier} into {neighbor_hallway.identifier}.")
                        for block in short_h.blocks:
                            block.area_uid = neighbor_hallway.unique_id
                        neighbor_hallway.blocks.extend(short_h.blocks)

                        # Clean up the now-empty short hallway and the connecting passage.
                        the_map.hallways.remove(short_h)
                        the_map.passages.remove(passage)

                        # Remove the passage from the blocks to allow wall regeneration.
                        b1, b2 = passage.side1, passage.side2
                        dir1 = _get_direction_from_move(b1, b2)
                        dir2 = _get_direction_from_move(b2, b1)
                        if dir1: setattr(b1, dir1, None)
                        if dir2: setattr(b2, dir2, None)
                        
                        # Regenerate walls for the affected blocks.
                        b1._set_initial_walls(the_map)
                        b2._set_initial_walls(the_map)
                        
                        made_a_merge = True
                        break  # Move to the next merge iteration.
            if made_a_merge:
                break
        
        if not made_a_merge:
            # If no merges were made in a full pass, stop.
            print("No more short hallways to merge.")
            break
    
    print("Finished merging hallways.")

def _get_direction_from_move(block1: Block, block2: Block) -> str:
    """
    Determines the cardinal direction of movement from block1 to block2.
    This is a helper function used to correctly orient passages and walls.
    """
    dx = block2.location.x - block1.location.x
    dy = block2.location.y - block1.location.y
    if dx == 1: return 'east'
    if dx == -1: return 'west'
    if dy == 1: return 'south'
    if dy == -1: return 'north'
    return None

def _connect_rooms_to_maze(the_map):
    """
    Ensures every room has at least one passage connecting it to a maze hallway.
    This function identifies all possible connection points between rooms and the maze
    and creates a door at one of these points for each room.
    """
    print("Connecting rooms to maze...")
    maze_hallway_uids = {h.unique_id for h in the_map.hallways if h.identifier.startswith('H')}
    if not maze_hallway_uids:
        print("Warning: No maze hallways found to connect rooms to.")
        return

    for room in the_map.rooms:
        # Check if the room is already connected to the maze.
        is_connected = False
        for passage in the_map.passages:
            if (passage.side1.area_uid == room.unique_id and passage.side2.area_uid in maze_hallway_uids) or \
               (passage.side2.area_uid == room.unique_id and passage.side1.area_uid in maze_hallway_uids):
                is_connected = True
                break
        
        if is_connected:
            continue

        # Find all potential locations for a new door.
        potential_doors = []
        for r_block in room.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor = the_map.get_block_at(r_block.location.x + dx, r_block.location.y + dy)
                if neighbor and neighbor.area_uid in maze_hallway_uids:
                    potential_doors.append((r_block, neighbor, direction))
        
        # Create a door at a random suitable location.
        if potential_doors:
            door_block1, door_block2, door_direction = random.choice(potential_doors)
            Passage.create(the_map, door_block1, door_block2, door_direction, is_door=True)
            print(f"Connected Room {room.identifier} to the maze.")
        else:
            print(f"Warning: Could not find a suitable wall to connect Room {room.identifier} to the maze.")