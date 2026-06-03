"""
This module contains the functions for generating hallways to connect rooms.
"""
import random
from .hallway import Hallway
from .passage import Passage
from .wall import Wall
from .utils import get_center_of_blocks, find_path_astar, heuristic

def generate_hallway_layout(the_map, hallway_count):
    """
    Connects all rooms on the map with hallways using a Minimum Spanning Tree (MST).
    This function first builds an MST to determine the connections between rooms,
    then creates hallways along these connections. Finally, it ensures that all
    rooms and hallways are properly connected with passages.
    """
    connections = _create_minimum_spanning_tree(the_map)
    print(f"MST determined {len(connections)} connections to be made.")
    
    for room1, room2 in connections:
        hallway_count = _create_hallway_between_rooms(the_map, room1, room2, hallway_count)
    
    # After creating hallways, ensure passages are correctly placed.
    for room in the_map.rooms:
        _ensure_room_passages(the_map, room)
    for hallway in the_map.hallways:
        _ensure_hallway_passages(the_map, hallway)
        
    return hallway_count

def _create_minimum_spanning_tree(the_map):
    """
    Builds a Minimum Spanning Tree (MST) of rooms to ensure all are connected.
    This function uses Kruskal's algorithm, where rooms are nodes and potential
    hallways are edges weighted by the distance between room centers.
    """
    if len(the_map.rooms) < 2:
        return []

    # Create a list of all possible connections (edges) between rooms.
    edges = []
    nodes = the_map.rooms
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            center1 = get_center_of_blocks(nodes[i].blocks)
            center2 = get_center_of_blocks(nodes[j].blocks)
            distance = heuristic(center1, center2)
            edges.append((distance, nodes[i], nodes[j]))
    
    # Sort edges by distance to prioritize shorter connections.
    edges.sort(key=lambda x: x[0])
    
    # Kruskal's algorithm to build the MST.
    parent = {room.unique_id: room.unique_id for room in nodes}
    def find_set(room_uid):
        if parent[room_uid] == room_uid:
            return room_uid
        parent[room_uid] = find_set(parent[room_uid])  # Path compression
        return parent[room_uid]

    def unite_sets(uid1, uid2):
        root1 = find_set(uid1)
        root2 = find_set(uid2)
        if root1 != root2:
            parent[root2] = root1

    mst_connections = []
    for distance, room1, room2 in edges:
        if find_set(room1.unique_id) != find_set(room2.unique_id):
            unite_sets(room1.unique_id, room2.unique_id)
            mst_connections.append((room1, room2))

    return mst_connections

def _create_hallway_between_rooms(the_map, room1, room2, hallway_count):
    """
    Creates a hallway between two rooms, if a path can be found.
    This function uses A* pathfinding to find a route and then converts
    the path into a hallway.
    """
    start_block = random.choice(room1.blocks)
    end_block = random.choice(room2.blocks)
    
    path = find_path_astar(the_map, (start_block.location.x, start_block.location.y), (end_block.location.x, end_block.location.y))
    
    if path and len(path) > 1:  # A path needs at least two points.
        hallway_count += 1
        new_hallway = Hallway(identifier=f"H{hallway_count}", connects_rooms=(room1.unique_id, room2.unique_id))
        
        blocks_for_hallway = []
        for loc in path:
            block = the_map.get_block_at(loc[0], loc[1])
            if block and block.empty:
                block.area_uid = new_hallway.unique_id
                block.empty = False
                blocks_for_hallway.append(block)
        
        if blocks_for_hallway:
            new_hallway.blocks = blocks_for_hallway
            the_map.add_hallway(new_hallway)
            for block in blocks_for_hallway:
                block._set_initial_walls(the_map)
            print(f"Created {new_hallway.identifier} between Room {room1.identifier} and Room {room2.identifier}.")
        else:
            # If no blocks were converted, the hallway is invalid, so decrement the count.
            hallway_count -= 1
            
    return hallway_count

def _ensure_room_passages(the_map, room):
    """
    Ensures a room has at least one passage, creating one if none exist.
    This function checks if a room is isolated, and if so, it finds a suitable
    location to create a passage to an adjacent room.
    """
    if room.count_passages(the_map) == 0:
        print(f"Room {room.identifier} has no passages. Searching for a place to add one.")
        
        # Collect all potential connection points.
        possible_connections = []
        for r_block in room.blocks:
            for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
                neighbor = the_map.get_block_at(r_block.location.x + dx, r_block.location.y + dy)
                if neighbor and not neighbor.empty and neighbor.area_uid != room.unique_id:
                    neighbor_area = the_map.get_area_by_uid(neighbor.area_uid)
                    # We are looking for connections to other rooms specifically.
                    if isinstance(neighbor_area, type(room)):
                        possible_connections.append((room, neighbor_area))

        # If there are possible connections, choose one to create a passage.
        if possible_connections:
            room1, room2 = random.choice(possible_connections)
            if _create_passage_between_adjacent_rooms(the_map, room1, room2):
                print(f"Successfully created a passage between Room {room1.identifier} and Room {room2.identifier}.")
                return

        print(f"Could not find a suitable location to add a passage for Room {room.identifier}.")

def _ensure_hallway_passages(the_map, hallway):
    """
    Ensures a hallway connects to its designated rooms, creating passages if necessary.
    This function checks if the hallway has fewer than two passages, which would indicate
    it's not properly connected. If so, it attempts to create passages to the rooms it's
    supposed to connect.
    """
    # This check is a potential source of issues. If a hallway is long, it might naturally have
    # more than two passages, but this function assumes that fewer than two is a problem.
    # It's a simple heuristic that might need refinement in the future.
    if hallway.count_passages(the_map) < 2:
        print(f"Hallway {hallway.identifier} has fewer than 2 passages. Attempting to add connections.")
        for room_uid in hallway.connects_rooms:
            _create_passage_between_hallway_and_room(the_map, hallway, room_uid)

def _create_passage_between_hallway_and_room(the_map, hallway, room_uid):
    """
    Creates a passage between a hallway and a room if one does not already exist.
    This function identifies the best location for a passage by checking for a direct
    physical connection (a wall) between the hallway and the target room. If a suitable
    location is found, it creates a passage, ensuring that the hallway is properly
    connected.
    """
    # Check if a passage already exists between the hallway and the room.
    for h_block in hallway.blocks:
        for direction in ['north', 'south', 'east', 'west']:
            connection = getattr(h_block, direction)
            if isinstance(connection, Passage):
                # A passage exists, check if it connects to the target room.
                if (connection.side1.area_uid == room_uid and connection.side2.area_uid == hallway.unique_id) or \
                   (connection.side2.area_uid == room_uid and connection.side1.area_uid == hallway.unique_id):
                    return False  # A passage already exists.

    # Find the best candidate location for a new passage.
    best_candidate = None
    for h_block in hallway.blocks:
        for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
            neighbor = the_map.get_block_at(h_block.location.x + dx, h_block.location.y + dy)
            if neighbor and neighbor.area_uid == room_uid:
                connection = getattr(h_block, direction)
                if isinstance(connection, Wall):
                    # This is a prime candidate, a wall directly between hallway and room.
                    best_candidate = (h_block, neighbor, direction)
                    break  # Found a wall, no need to search further from this block.
        if best_candidate:
            break  # Found a candidate, proceed to create the passage.

    # Create a passage at the best candidate location.
    if best_candidate:
        h_block, neighbor, direction = best_candidate
        Passage.create(the_map, h_block, neighbor, direction, is_door=True)
        return True

    return False

def _create_passage_between_adjacent_rooms(the_map, room1, room2):
    """
    Creates a passage between two adjacent rooms, if one doesn't already exist.
    This function finds a suitable wall to replace with a passage.
    """
    # First, check if a passage already exists to avoid duplicates.
    for r1_block in room1.blocks:
        for direction in ['north', 'south', 'east', 'west']:
            connection = getattr(r1_block, direction)
            if isinstance(connection, Passage):
                if (connection.side1.area_uid == room2.unique_id or connection.side2.area_uid == room2.unique_id):
                    return False  # A passage already exists.

    # If no passage exists, find a suitable location and create one.
    for r1_block in room1.blocks:
        for direction, (dx, dy) in {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}.items():
            neighbor = the_map.get_block_at(r1_block.location.x + dx, r1_block.location.y + dy)
            if neighbor and neighbor.area_uid == room2.unique_id:
                if isinstance(getattr(r1_block, direction), Wall):
                    Passage.create(the_map, r1_block, neighbor, direction, is_door=True)
                    return True
    return False