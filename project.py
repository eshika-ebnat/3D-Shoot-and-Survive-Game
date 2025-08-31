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
## Camera (third-person)
= 140.0
follow_height = 140.0
cam_x, cam _y, cam_z = 0.0, -400.0, 250.0

## Weapons and Ammo Details
weapons = {
    "pistol":       {"mag": 12, "fire_cd": 0.22, "bullet_spd": 1200.0, "dmg": 1.0, "type": "bullet"},
    "rifle":        {"mag": 30, "fire_cd": 0.10, "bullet_spd": 1600.0, "dmg": 0.7, "type": "bullet"},
    "machine_gun":  {"mag": 60, "fire_cd": 0.05, "bullet_spd": 1800.0, "dmg": 0.5, "type": "bullet"},
    "rocket":       {"mag": 4,  "fire_cd": 0.70, "bullet_spd": 1000.0, "dmg": 0.0, "type": "rocket"},
}
current_weapon = "pistol"
owned_weapons = {"pistol"}
ammo_in_mag_by_weapon = {"pistol": weapons["pistol"]["mag"], "rifle": 0, "machine_gun": 0, "rocket": 0}
ammo_in_mag = ammo_in_mag_by_weapon[current_weapon]
ammo_reserve = {"pistol": 72, "rifle": 120, "machine_gun": 180, "rocket": 12}
reloading = False
reload_time = 1.25
reload_timer = 0.0
fire_cooldown = 0.0
bullets  = []
rockets  = []
BULLET_RADIUS = 6.0  

## Grenades and Explosions
grenades = []
GRENADE_THROW_SPEED = 700.0
GRENADE_FUSE = 1.2
EXPLOSION_RADIUS = 220.0
GRENADE_EXPLOSION_RADIUS = 300.0
explosions = []
EXPLOSION_TTL = 0.60


































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