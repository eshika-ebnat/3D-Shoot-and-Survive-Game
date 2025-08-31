from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import math, random, time

## Window dimensions and aspect ratio
WINDOW_W, WINDOW_H = 1280, 650
ASPECT = WINDOW_W / WINDOW_H
GRID_LENGTH = 1400
fovY_default = 120.0
fovY_zoom = 30.0
fovY_zoom_3p = 90.0  # mild zoom in 3P

first_person = False
scope_active = False
fire_pressed = False  # fire cooldown

## Player variables
player_pos = [0.0, 0.0, 10.0]
player_angle = 0.0
player_on_ground = True
vz = 0.0
GRAVITY = -1800.0
JUMP_VELOCITY = 700.0
MOVE_STEP = 28.0
STEP_MAX = 12.0
PLAYER_RADIUS = 26.0  
health = 100
max_health = 100
landing_flash = 0.0

## player movement
keys_down = set()
MOVE_SPEED = 400.0
TURN_SPEED = 100.0

































def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Shoot & Survive - 3D Game")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(on_key_down)
    glutKeyboardUpFunc(on_key_up)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    reset_game()
    glutMainLoop()

if __name__ == "__main__":
    main()