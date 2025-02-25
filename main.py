import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

camera_x = 0.0
camera_y = 0.0
camera_z = -5.0
move_speed = 0.1

def draw_wireframe_cube():
    """Draws a simple wireframe cube centered at (0,0,0)."""
    glColor3f(1, 1, 1)  # Make sure lines are white
    glLineWidth(2)      # Thicker lines so they're visible
    glBegin(GL_LINES)
    # -- Define 12 edges of the cube (24 vertices total) --
    glVertex3f(-1.0, -1.0,  1.0)
    glVertex3f( 1.0, -1.0,  1.0)

    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f( 1.0,  1.0,  1.0)

    glVertex3f( 1.0,  1.0,  1.0)
    glVertex3f(-1.0,  1.0,  1.0)

    glVertex3f(-1.0,  1.0,  1.0)
    glVertex3f(-1.0, -1.0,  1.0)

    # Back face
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f( 1.0, -1.0, -1.0)

    glVertex3f( 1.0, -1.0, -1.0)
    glVertex3f( 1.0,  1.0, -1.0)

    glVertex3f( 1.0,  1.0, -1.0)
    glVertex3f(-1.0,  1.0, -1.0)

    glVertex3f(-1.0,  1.0, -1.0)
    glVertex3f(-1.0, -1.0, -1.0)

    # Connect front and back faces
    glVertex3f(-1.0, -1.0,  1.0)
    glVertex3f(-1.0, -1.0, -1.0)

    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f( 1.0, -1.0, -1.0)

    glVertex3f( 1.0,  1.0,  1.0)
    glVertex3f( 1.0,  1.0, -1.0)

    glVertex3f(-1.0,  1.0,  1.0)
    glVertex3f(-1.0,  1.0, -1.0)

    glEnd()

def main():
    global camera_x, camera_y, camera_z

    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Wireframe Cube - WASD Controls")

    # --- NEW: Setup Clear Color (black) and enable Depth Test ---
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)

    # --- Properly separate projection and modelview matrices ---
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    width, height = display
    gluPerspective(45, (width/height), 0.1, 50.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    clock = pygame.time.Clock()
    running = True

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        # WASD movement
        if keys[pygame.K_w]:
            camera_z += move_speed
        if keys[pygame.K_s]:
            camera_z -= move_speed
        if keys[pygame.K_a]:
            camera_x += move_speed
        if keys[pygame.K_d]:
            camera_x -= move_speed
        # Q/E for vertical
        if keys[pygame.K_q]:
            camera_y -= move_speed
        if keys[pygame.K_e]:
            camera_y += move_speed

        # Clear screen and depth buffer
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Reset transformations
        glLoadIdentity()

        # Move "camera" by translating in the opposite direction
        glTranslatef(camera_x, camera_y, camera_z)

        # Draw the wireframe cube
        draw_wireframe_cube()

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()