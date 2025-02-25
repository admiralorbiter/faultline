import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import numpy as np

# Game state and settings
class GameState:
    def __init__(self):
        # Aircraft state
        self.position = [0.0, 0.0, 0.0]
        self.rotation = [0.0, 180.0, 0.0]  # [pitch, yaw, roll] in degrees
        self.velocity = [0.0, 0.0, 0.0]
        self.throttle = 0.0  # 0.0 to 1.0
        
        # Camera settings
        self.camera_distance = -10.0
        self.camera_offset = [0.0, 1.5, 0.0]
        self.camera_rotation = [0.0, 0.0, 0.0]
        
        # Flight model parameters
        self.max_speed = 2.0
        self.lift_coefficient = 0.02
        self.drag_coefficient = 0.008
        self.gravity = 0.01
        
        # System status
        self.engine_temperature = 0.0  # 0.0 to 1.0
        self.engine_overheat_threshold = 0.8
        self.engine_cooling_rate = 0.01
        self.engine_heating_rate = 0.03
        self.engine_overheated = False
        
        # Environment
        self.terrain_size = 50  # Reduced size for better visibility
        self.terrain_grid_size = 10  # Smaller grid for more detail
        self.terrain_chunks = {}  # Dictionary to store terrain chunks
        self.current_chunk = None  # Initialize as None to force first update

# Aircraft Geometry
def create_aircraft():
    """Create a geometric representation of the aircraft"""
    vertices = [
        # Fuselage (triangular prism)
        [0.0, 0.0, 2.0],    # Nose
        [-0.5, -0.5, 0.0],  # Bottom left
        [0.5, -0.5, 0.0],   # Bottom right
        [0.0, 0.5, 0.0],    # Top
        
        # Wings
        [-3.0, 0.0, 0.0],   # Left wingtip
        [3.0, 0.0, 0.0],    # Right wingtip
        
        # Tail
        [0.0, 0.5, -2.0],   # Tail top
        [-1.0, 0.0, -2.0],  # Tail left
        [1.0, 0.0, -2.0]    # Tail right
    ]
    
    edges = [
        # Fuselage
        (0, 1), (0, 2), (0, 3),
        (1, 2), (2, 3), (3, 1),
        
        # Wings
        (1, 4), (4, 3),
        (2, 5), (5, 3),
        
        # Tail
        (3, 6),
        (1, 7), (7, 6),
        (2, 8), (8, 6)
    ]
    
    return vertices, edges

def draw_aircraft(vertices, edges, solid=False):
    """Draw the aircraft using either wireframe or solid geometry"""
    if solid:
        # Draw as solid triangles
        glBegin(GL_TRIANGLES)
        # Fuselage
        glColor3f(0.7, 0.7, 0.7)
        glVertex3fv(vertices[0])
        glVertex3fv(vertices[1])
        glVertex3fv(vertices[2])
        
        glVertex3fv(vertices[0])
        glVertex3fv(vertices[2])
        glVertex3fv(vertices[3])
        
        glVertex3fv(vertices[0])
        glVertex3fv(vertices[3])
        glVertex3fv(vertices[1])
        
        glVertex3fv(vertices[1])
        glVertex3fv(vertices[2])
        glVertex3fv(vertices[3])
        
        # Wings - left
        glColor3f(0.6, 0.6, 0.6)
        glVertex3fv(vertices[1])
        glVertex3fv(vertices[4])
        glVertex3fv(vertices[3])
        
        # Wings - right
        glVertex3fv(vertices[2])
        glVertex3fv(vertices[5])
        glVertex3fv(vertices[3])
        
        # Tail
        glColor3f(0.5, 0.5, 0.5)
        glVertex3fv(vertices[3])
        glVertex3fv(vertices[6])
        glVertex3fv(vertices[7])
        
        glVertex3fv(vertices[3])
        glVertex3fv(vertices[6])
        glVertex3fv(vertices[8])
        glEnd()
    else:
        # Draw as wireframe
        glBegin(GL_LINES)
        glColor3f(1.0, 1.0, 1.0)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()

# Environment Generation
def generate_terrain_chunk(chunk_x, chunk_z, size, grid_size):
    """Generate a terrain chunk for the given coordinates"""
    vertices = []
    edges = []
    
    # Calculate chunk offset
    offset_x = chunk_x * size * 2
    offset_z = chunk_z * size * 2
    
    # Create a grid of points
    points_per_side = (size * 2) // grid_size + 1  # Added +1 to close the grid
    for z in range(-size, size + grid_size, grid_size):  # Added + grid_size to include last point
        for x in range(-size, size + grid_size, grid_size):  # Added + grid_size to include last point
            # Use absolute world coordinates for height calculation
            world_x = x + offset_x
            world_z = z + offset_z
            # Simple height function (more pronounced terrain)
            height = math.sin(world_x * 0.05) * math.cos(world_z * 0.05) * 3.0
            vertices.append([x + offset_x, height, z + offset_z])
    
    # Connect points to form a grid of lines
    width = points_per_side
    for z in range(width - 1):
        for x in range(width - 1):
            idx = z * width + x
            # Horizontal and vertical lines
            edges.append((idx, idx + 1))
            edges.append((idx, idx + width))
    
    return vertices, edges

def update_terrain_chunks(game_state):
    """Update visible terrain chunks based on player position"""
    # Calculate current chunk coordinates
    chunk_x = int(game_state.position[0] / (game_state.terrain_size * 2))
    chunk_z = int(game_state.position[2] / (game_state.terrain_size * 2))
    
    # If we've moved to a new chunk or first initialization
    if game_state.current_chunk is None or (chunk_x, chunk_z) != game_state.current_chunk:
        game_state.current_chunk = (chunk_x, chunk_z)
        
        # Generate new chunks in a 5x5 grid around player for better visibility
        for x in range(chunk_x - 2, chunk_x + 3):
            for z in range(chunk_z - 2, chunk_z + 3):
                if (x, z) not in game_state.terrain_chunks:
                    game_state.terrain_chunks[(x, z)] = generate_terrain_chunk(
                        x, z, game_state.terrain_size, game_state.terrain_grid_size
                    )
        
        # Remove chunks that are too far away
        chunks_to_remove = []
        for chunk_coords in game_state.terrain_chunks:
            if abs(chunk_coords[0] - chunk_x) > 2 or abs(chunk_coords[1] - chunk_z) > 2:
                chunks_to_remove.append(chunk_coords)
        
        for chunk_coords in chunks_to_remove:
            del game_state.terrain_chunks[chunk_coords]

def draw_terrain(game_state):
    """Draw all visible terrain chunks"""
    glLineWidth(1.0)  # Set line width for terrain grid
    glBegin(GL_LINES)
    glColor3f(0.2, 0.5, 0.2)  # Green tint for ground
    
    # Draw all chunks
    for chunk_vertices, chunk_edges in game_state.terrain_chunks.values():
        for edge in chunk_edges:
            for vertex in edge:
                glVertex3fv(chunk_vertices[vertex])
    glEnd()

# HUD Rendering
def draw_hud(game_state, width, height):
    """Draw the Heads-Up Display with flight information"""
    # Switch to orthographic projection for 2D drawing
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, height, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    
    # Throttle indicator (left side)
    throttle_height = int(height * 0.6)
    throttle_width = 20
    throttle_x = 30
    throttle_y = (height - throttle_height) // 2
    
    # Throttle background
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(throttle_x, throttle_y)
    glVertex2f(throttle_x + throttle_width, throttle_y)
    glVertex2f(throttle_x + throttle_width, throttle_y + throttle_height)
    glVertex2f(throttle_x, throttle_y + throttle_height)
    glEnd()
    
    # Throttle level
    throttle_level = int(throttle_height * game_state.throttle)
    glColor3f(0.0, 0.8, 0.0)  # Green for normal operation
    
    # If engine is overheated, make throttle indicator red
    if game_state.engine_overheated:
        glColor3f(1.0, 0.0, 0.0)  # Red for overheated
    
    glBegin(GL_QUADS)
    glVertex2f(throttle_x, throttle_y + throttle_height - throttle_level)
    glVertex2f(throttle_x + throttle_width, throttle_y + throttle_height - throttle_level)
    glVertex2f(throttle_x + throttle_width, throttle_y + throttle_height)
    glVertex2f(throttle_x, throttle_y + throttle_height)
    glEnd()
    
    # Engine temperature indicator (right side)
    temp_height = int(height * 0.6)
    temp_width = 20
    temp_x = width - 50
    temp_y = (height - temp_height) // 2
    
    # Temperature background
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(temp_x, temp_y)
    glVertex2f(temp_x + temp_width, temp_y)
    glVertex2f(temp_x + temp_width, temp_y + temp_height)
    glVertex2f(temp_x, temp_y + temp_height)
    glEnd()
    
    # Temperature level
    temp_level = int(temp_height * game_state.engine_temperature)
    
    # Color gradient from green to red based on temperature
    temp_color = [
        min(1.0, game_state.engine_temperature * 2),  # Red increases with temp
        max(0.0, 1.0 - game_state.engine_temperature * 1.5),  # Green decreases with temp
        0.0  # No blue
    ]
    glColor3f(*temp_color)
    
    glBegin(GL_QUADS)
    glVertex2f(temp_x, temp_y + temp_height - temp_level)
    glVertex2f(temp_x + temp_width, temp_y + temp_height - temp_level)
    glVertex2f(temp_x + temp_width, temp_y + temp_height)
    glVertex2f(temp_x, temp_y + temp_height)
    glEnd()
    
    # Warning indicator if overheated
    if game_state.engine_overheated:
        warning_x = width // 2
        warning_y = 50
        warning_size = 30
        
        # Blinking warning
        if pygame.time.get_ticks() % 1000 < 500:
            glColor3f(1.0, 0.0, 0.0)
            glLineWidth(3)
            
            # Triangle warning symbol
            glBegin(GL_LINE_LOOP)
            glVertex2f(warning_x, warning_y - warning_size)
            glVertex2f(warning_x + warning_size, warning_y + warning_size)
            glVertex2f(warning_x - warning_size, warning_y + warning_size)
            glEnd()
            
            # Exclamation mark
            glBegin(GL_LINES)
            glVertex2f(warning_x, warning_y - warning_size//2)
            glVertex2f(warning_x, warning_y + warning_size//2)
            glEnd()
            
            glBegin(GL_POINTS)
            glVertex2f(warning_x, warning_y + warning_size//1.5)
            glEnd()
    
    # Restore 3D settings
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# Flight Physics
def update_flight_physics(game_state, delta_time):
    """Update aircraft position and orientation based on physics"""
    # Convert rotations to radians for trig calculations
    pitch_rad = math.radians(game_state.rotation[0])
    yaw_rad = math.radians(game_state.rotation[1])
    roll_rad = math.radians(game_state.rotation[2])
    
    # Calculate direction vector based on aircraft orientation
    direction = [
        math.sin(yaw_rad) * math.cos(pitch_rad),
        math.sin(pitch_rad),
        math.cos(yaw_rad) * math.cos(pitch_rad)
    ]
    
    # Calculate lift based on speed and pitch
    speed = math.sqrt(sum(v*v for v in game_state.velocity))
    angle_of_attack = max(0, math.cos(pitch_rad))  # Most lift when level, less when pitched up too much
    lift = game_state.lift_coefficient * speed * angle_of_attack * math.cos(roll_rad)
    
    # Apply throttle (reduced if engine is overheated)
    throttle_factor = game_state.throttle
    if game_state.engine_overheated:
        throttle_factor *= 0.5
    
    # Apply forces
    for i in range(3):
        # Thrust in direction of aircraft
        game_state.velocity[i] += direction[i] * throttle_factor * 0.02  # Reduced thrust factor
        
        # Gravity (always down on Y axis)
        if i == 1:  # Y axis
            game_state.velocity[i] -= game_state.gravity
            game_state.velocity[i] += lift
        
        # Apply drag (opposite to velocity)
        if game_state.velocity[i] != 0:
            drag = game_state.drag_coefficient * game_state.velocity[i] * abs(game_state.velocity[i])
            game_state.velocity[i] -= drag
    
    # Update position based on velocity
    for i in range(3):
        game_state.position[i] += game_state.velocity[i]
    
    # Update engine temperature based on throttle
    if game_state.throttle > 0.5:
        # Engine heats up at high throttle
        game_state.engine_temperature += game_state.engine_heating_rate * (game_state.throttle - 0.5) * 2 * delta_time
    else:
        # Engine cools down at low throttle
        game_state.engine_temperature -= game_state.engine_cooling_rate * delta_time
    
    # Clamp engine temperature
    game_state.engine_temperature = max(0.0, min(1.0, game_state.engine_temperature))
    
    # Check for engine overheat
    if game_state.engine_temperature >= game_state.engine_overheat_threshold:
        game_state.engine_overheated = True
    elif game_state.engine_temperature < game_state.engine_overheat_threshold * 0.7:
        # Only reset when cooled down significantly
        game_state.engine_overheated = False

def handle_input(game_state, keys, delta_time):
    """Process keyboard input for flight controls"""
    # Pitch (W/S)
    if keys[pygame.K_w]:
        game_state.rotation[0] += 1.0 * delta_time * 60  # Pitch up
    if keys[pygame.K_s]:
        game_state.rotation[0] -= 1.0 * delta_time * 60  # Pitch down
    
    # Roll (A/D)
    if keys[pygame.K_a]:
        game_state.rotation[2] -= 1.5 * delta_time * 60  # Roll left
    if keys[pygame.K_d]:
        game_state.rotation[2] += 1.5 * delta_time * 60  # Roll right
    
    # Yaw (Q/E)
    if keys[pygame.K_q]:
        game_state.rotation[1] -= 1.0 * delta_time * 60  # Yaw left
    if keys[pygame.K_e]:
        game_state.rotation[1] += 1.0 * delta_time * 60  # Yaw right
    
    # Throttle (Up/Down arrow)
    if keys[pygame.K_UP]:
        game_state.throttle = min(1.0, game_state.throttle + 0.01 * delta_time * 60)
    if keys[pygame.K_DOWN]:
        game_state.throttle = max(0.0, game_state.throttle - 0.01 * delta_time * 60)
    
    # Reset position (R)
    if keys[pygame.K_r]:
        game_state.position = [0.0, 10.0, 0.0]
        game_state.rotation = [0.0, 0.0, 0.0]
        game_state.velocity = [0.0, 0.0, 0.0]
        game_state.throttle = 0.0
        game_state.engine_temperature = 0.0
        game_state.engine_overheated = False

def main():
    pygame.init()
    display = (1024, 768)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Faultline Flight - Proof of Concept")
    
    # Initialize OpenGL
    glClearColor(0.05, 0.05, 0.1, 1.0)  # Dark blue background
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    
    # Set up perspective
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (display[0]/display[1]), 0.1, 1000.0)
    
    # Initialize game state
    game_state = GameState()
    game_state.position = [0.0, 10.0, 0.0]  # Start above ground
    game_state.velocity = [0.0, 0.0, 1.0]  # Initial forward velocity
    game_state.throttle = 0.5  # Start with some throttle
    
    # Create aircraft geometry
    aircraft_vertices, aircraft_edges = create_aircraft()
    
    # Initialize terrain
    update_terrain_chunks(game_state)
    
    # Main game loop
    clock = pygame.time.Clock()
    wireframe_mode = True
    running = True
    
    while running:
        # Calculate delta time
        delta_time = clock.tick(60) / 1000.0  # seconds since last frame
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Toggle wireframe mode with Tab
                if event.key == pygame.K_TAB:
                    wireframe_mode = not wireframe_mode
        
        # Get keyboard state
        keys = pygame.key.get_pressed()
        
        # Handle input
        handle_input(game_state, keys, delta_time)
        
        # Update physics
        update_flight_physics(game_state, delta_time)
        
        # Update terrain chunks based on player position
        update_terrain_chunks(game_state)
        
        # Clear the screen and depth buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Set up the camera
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        # Position the camera behind and slightly above the aircraft
        # Calculate the camera position based on aircraft orientation
        pitch_rad = math.radians(game_state.rotation[0])
        yaw_rad = math.radians(game_state.rotation[1])
        
        camera_distance = game_state.camera_distance
        camera_height = game_state.camera_offset[1]
        
        camera_x = game_state.position[0] - math.sin(yaw_rad) * camera_distance
        camera_y = game_state.position[1] + camera_height
        camera_z = game_state.position[2] - math.cos(yaw_rad) * camera_distance
        
        # Look at the aircraft
        gluLookAt(
            camera_x, camera_y, camera_z,
            game_state.position[0], game_state.position[1], game_state.position[2],
            0, 1, 0
        )
        
        # Draw terrain
        glPushMatrix()
        draw_terrain(game_state)
        glPopMatrix()
        
        # Draw aircraft
        glPushMatrix()
        glTranslatef(*game_state.position)
        
        # Apply rotations in the correct order: yaw, pitch, roll
        glRotatef(game_state.rotation[1], 0, 1, 0)  # Yaw
        glRotatef(game_state.rotation[0], 1, 0, 0)  # Pitch
        glRotatef(game_state.rotation[2], 0, 0, 1)  # Roll
        
        # If engine is overheated, make aircraft blink red in wireframe mode
        if game_state.engine_overheated and wireframe_mode:
            if pygame.time.get_ticks() % 500 < 250:
                glColor3f(1.0, 0.0, 0.0)  # Red for overheated
        
        draw_aircraft(aircraft_vertices, aircraft_edges, not wireframe_mode)
        glPopMatrix()
        
        # Draw HUD
        draw_hud(game_state, *display)
        
        # Display FPS and flight info on screen (debug text)
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()