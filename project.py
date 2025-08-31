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
follow_dist = 140.0
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

## Enemy variables
enemies = []
wave = 1
ENEMY_BASE_SPEED = 80.0
ENEMY_RADIUS = 40.0
ENEMY_BASE_HP = 2
SPAWN_BOX = GRID_LENGTH - 120
enemy_spin_phase = 0.0
ENEMY_CONTACT_DAMAGE = {
    "drone": 8,  
    "grunt": 12,  
    "brute": 24  
}
## Pickups
pickups = []
PICKUP_RADIUS = 24.0
pickup_bob_phase = 0.0
PICKUP_FLOAT_BASE_Z = 28.0
PICKUP_BOB_AMPLITUDE = 10.0

# Timed weapon spawns
GUN_SPAWN_INTERVAL = 15.0
gun_spawn_timer = 0.0
MAX_WEAPON_PICKUPS = 4

## Rocks
ROCKS = []
NUM_ROCKS = 18
ROCK_MIN, ROCK_MAX = 60, 140

## Score Variables
score = 0
paused = False
game_over = False

## Laser variables
LASER_INTERVAL = 30.0
LASER_SWEEP_TIME = 5.0
LASER_THICKNESS = 120.0
LASER_GLOW_THICKNESS = 180.0
laser_timer = LASER_INTERVAL
laser_active = False
laser_t = 0.0

## Drawing Functions

# Draw text on screen
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def forward_vec(deg):
    r = math.radians(deg)
    return (-math.sin(r), math.cos(r))  

def clamp2D(x, y):
    half = GRID_LENGTH - 20
    return max(-half, min(half, x)), max(-half, min(half, y))

def dist2(x1,y1,x2,y2):
    dx, dy = x1-x2, y1-y2
    return dx*dx + dy*dy

def hash01(x, y):
    return 0.5 + 0.5 * math.sin(x*12.9898 + y*78.233)

## Grass and Rocks
def draw_grass_tuft(x, y):
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y, 8.0)
    for i, ang in enumerate((0, 25, -25)):
        glPushMatrix()
        glRotatef(ang, 0, 0, 1)
        glRotatef(-90, 1, 0, 0)
        glColor3f(0.12 + 0.02*i, 0.55 + 0.04*i, 0.18)
        gluCylinder(q, 0.9, 0.6, 18.0 + 2.0*i, 8, 1)
        glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 18.0)
    glColor3f(0.12, 0.55, 0.18)
    glutSolidSphere(2.0, 10, 8)
    glPopMatrix()
    glPopMatrix()

def draw_grass_ground():
    step = 200
    half = GRID_LENGTH
    for iy in range(-half, half, step):
        for ix in range(-half, half, step):
            cx = ix + step * 0.5
            cy = iy + step * 0.5
            chk = ((ix // step) + (iy // step)) & 1
            v = hash01(ix * 0.01, iy * 0.01)
            base_g = 0.35 if chk == 0 else 0.42
            g = base_g + (v - 0.5) * 0.10
            r = 0.07 + (v - 0.5) * 0.02
            b = 0.06 + (v - 0.5) * 0.015

            glPushMatrix()
            glTranslatef(cx, cy, 0.0)
            glScalef(1.0, 1.0, 0.04)
            glColor3f(max(0.0, r), max(0.0, g), max(0.0, b))
            glutSolidCube(step)
            glPopMatrix()

            if hash01(ix * 0.2, iy * 0.2) > 0.86:
                ox = (hash01(ix + 1.7, iy + 3.1) - 0.5) * (step * 0.4)
                oy = (hash01(ix + 5.3, iy + 2.9) - 0.5) * (step * 0.4)
                draw_grass_tuft(cx + ox, cy + oy)

GROUND_BASE_Z = 4.0  # top surface grass tiles


def ground_height_at(x, y):
    h = GROUND_BASE_Z
    for r in ROCKS:
        s = r["size"]
        half = s * 0.5
        if abs(x - r["x"]) <= half and abs(y - r["y"]) <= half:
            h = max(h, s)  # rock top z = s
    return h
































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