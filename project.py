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
cam_x, cam_y, cam_z = 0.0, -400.0, 250.0

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

# Helper rockss
def rock_at_point(x, y):
    best = None
    best_h = -1.0
    for r in ROCKS:
        half = r["size"] * 0.5
        if abs(x - r["x"]) <= half and abs(y - r["y"]) <= half:
            if r["size"] > best_h:
                best_h = r["size"]
                best = r
    return best

# Player vs rock collision 
def resolve_player_vs_rocks(nx, ny, pz, stepping_target_rock=None):
    for r in ROCKS:
        if r is stepping_target_rock:
            continue

        top_z = r["size"]
        if pz >= top_z - 1.0:
            continue

        half = r["size"] * 0.5
        minx = r["x"] - half - PLAYER_RADIUS
        maxx = r["x"] + half + PLAYER_RADIUS
        miny = r["y"] - half - PLAYER_RADIUS
        maxy = r["y"] + half + PLAYER_RADIUS

        if (nx >= minx and nx <= maxx and ny >= miny and ny <= maxy):
            dx_left   = nx - minx
            dx_right  = maxx - nx
            dy_bottom = ny - miny
            dy_top    = maxy - ny
            m = min(dx_left, dx_right, dy_bottom, dy_top)
            if m == dx_left:
                nx = minx
            elif m == dx_right:
                nx = maxx
            elif m == dy_bottom:
                ny = miny
            else:
                ny = maxy
    return nx, ny

# Rocks
def draw_rocks():
    q = gluNewQuadric()
    for r in ROCKS:
        s = r["size"]
        x, y = r["x"], r["y"]
        top = s * 0.5
        tone = 0.5 + 0.12 * hash01(x * 0.01, y * 0.01)
        cR = tone * 0.9; cG = tone; cB = tone * 0.72

        glPushMatrix()
        glTranslatef(x, y, top)
        glColor3f(cR, cG, cB)
        glutSolidCube(s)
        glPopMatrix()

        r1 = s * (0.28 + 0.06 * hash01(x + 11.0, y + 5.0))
        r2 = s * (0.24 + 0.06 * hash01(x + 7.0,  y + 13.0))
        o1x = (hash01(x + 2.0,  y + 3.0) - 0.5) * s * 0.35
        o1y = (hash01(x + 17.0, y + 9.0) - 0.5) * s * 0.35
        o2x = (hash01(x + 23.0, y + 19.0) - 0.5) * s * 0.30
        o2y = (hash01(x + 31.0, y + 29.0) - 0.5) * s * 0.30

        glPushMatrix()
        glTranslatef(x + o1x, y + o1y, top + s * 0.10)
        glColor3f(cR*0.99, cG*0.45, cB*0.25)
        gluSphere(q, r1, 16, 12)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(x + o2x, y + o2y, top + s * 0.05)
        glColor3f(cR*1.02, cG*1.02, cB*1.02)
        gluSphere(q, r2, 16, 12)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(x, y, s * 0.35)
        glRotatef(-90, 1, 0, 0)
        glColor3f(cR*0.92, cG*0.92, cB*0.92)
        gluCylinder(q, s*0.20, s*0.22, s*0.30, 12, 1)
        glPopMatrix()

        if hash01(x * 0.5, y * 0.5) > 0.7:
            mcount = 2 + int(hash01(x + 4.0, y + 6.0) * 3)
            for i in range(mcount):
                mx = (hash01(x + i*3.3, y + i*1.7) - 0.5) * s * 0.25
                my = (hash01(x + i*5.1, y + i*2.9) - 0.5) * s * 0.25
                mr = s * (0.04 + 0.02 * hash01(x + i*7.7, y + i*9.1))
                glPushMatrix()
                glTranslatef(x + mx, y + my, s - mr*0.6)
                glColor3f(0.14, 0.36 + 0.10*hash01(x+i, y-i), 0.18)
                glutSolidSphere(mr, 10, 8)
                glPopMatrix()

## Lifebar
def draw_lifebar_world(x, y, z, ratio, w=60.0, h=10.0):
    ratio = max(0.0, min(1.0, ratio))
    glDisable(GL_DEPTH_TEST)
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.10, 0.10, 0.10)
    glBegin(GL_QUADS)
    glVertex3f(-w/2 - 2, -2, 0)
    glVertex3f(w/2 + 2, -2, 0)
    glVertex3f(w/2 + 2, h + 2, 0)
    glVertex3f(-w/2 - 2, h + 2, 0)
    glEnd()

    glColor3f(0.28, 0.02, 0.02)
    glBegin(GL_QUADS)
    glVertex3f(-w/2, 0, 0)
    glVertex3f(w/2, 0, 0)
    glVertex3f(w/2, h, 0)
    glVertex3f(-w/2, h, 0)
    glEnd()

    glColor3f(0.12, 0.90, 0.35)
    ww = ratio * w
    glBegin(GL_QUADS)
    glVertex3f(-w/2, 0, 0)
    glVertex3f(-w/2 + ww, 0, 0)
    glVertex3f(-w/2 + ww, h, 0)
    glVertex3f(-w/2, h, 0)
    glEnd()

    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

## Draw Player and Enemies
def draw_player():
    q = gluNewQuadric()
    SHIRT  = (0.10, 0.35, 0.95)
    SLEEVE = (0.98, 0.55, 0.10)
    PANTS  = (0.62, 0.35, 0.25)
    SKIN   = (0.96, 0.82, 0.68)
    BARREL = (0.50, 0.50, 0.55)

    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], max(0.0, player_pos[2]))
    glRotatef(player_angle, 0, 0, 1)

    torso_size = 40.0
    glPushMatrix()
    glTranslatef(0, 0, 72)
    glScalef(1.0, 0.60, 1.10)
    glColor3f(*SHIRT)
    glutSolidCube(torso_size)
    glPopMatrix()

    torso_half_w = (torso_size * 1.0) * 0.5
    torso_half_h = (torso_size * 1.10) * 0.5

    glPushMatrix()
    glTranslatef(0, 0, 72 + torso_half_h + 12)
    glColor3f(0,0,0)
    gluSphere(q, 14, 16, 12)
    glPopMatrix()

    hip_z = 20 - torso_half_h + 2
    leg_h = 40.0; leg_r = 8.0; hip_x = 14.0
    for sgn in (-1, 1):
        glPushMatrix()
        glTranslatef(sgn*hip_x, 0, hip_z)
        glColor3f(*PANTS)
        gluCylinder(q, leg_r, leg_r, leg_h, 14, 1)
        glPopMatrix()

    shoulder_z = 68 + torso_half_h - 8
    arm_len    = 35.0; arm_r = 6.5
    shoulder_x = torso_half_w + arm_r*0.6+1
    inward_deg = 155.0

    glPushMatrix()
    glTranslatef(-shoulder_x, 20, shoulder_z)
    glRotatef(90, 1, 0, 0)
    glRotatef(inward_deg, 0, 1, 0)
    glColor3f(*SLEEVE)
    gluCylinder(q, arm_r, arm_r, arm_len, 25, 8)
    glTranslatef(-shoulder_x+30, arm_len-30, shoulder_z-39)
    glColor3f(*SKIN)
    gluSphere(q, arm_r*1.2, 14, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef( shoulder_x, 20, shoulder_z)
    glRotatef(90, 1, 0, 0)
    glRotatef(-inward_deg, 0, 1, 0)
    glColor3f(*SLEEVE)
    gluCylinder(q, arm_r, arm_r, arm_len, 25, 8)
    glTranslatef(shoulder_x-30, arm_len-30, shoulder_z-39)
    glColor3f(*SKIN)
    gluSphere(q, arm_r*1.2, 14, 12)
    glPopMatrix()

    gun_y = arm_len+20
    gun_z = shoulder_z
    glPushMatrix()
    glTranslatef(0, gun_y, gun_z)
    glRotatef(90, 0, 0, 1)
    glScalef(1.0, 0.25, 0.45)
    glColor3f(*BARREL)
    glutSolidCube(24)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, gun_y+7, gun_z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(*BARREL)
    gluCylinder(q, 6.0, 3.0, 28.0, 12, 1)
    glPopMatrix()

    glPopMatrix()

    glDisable(GL_DEPTH_TEST)
    head_z = player_pos[2] + 128
    draw_lifebar_world(player_pos[0], player_pos[1], head_z, health/max_health, w=70.0, h=10.0)
    glEnable(GL_DEPTH_TEST)


def draw_enemy(e):
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(e["x"], e["y"], e["z"])
    et = e.get("type", "grunt"); r = e["r"]

    if et == "drone":
        glColor3f(0.92, 0.18, 0.18)
        gluSphere(q, r*0.85, 18, 14)
        glPushMatrix(); 
        glTranslatef(0,0,r*0.90)
        glColor3f(0.35,0.35,0.38)
        gluCylinder(q, r*0.10, r*0.10, r*0.30, 12, 1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0,0,r*1.05)
        glRotatef(math.degrees(enemy_spin_phase)*220.0, 0, 0, 1)
        glColor3f(0.10,0.10,0.12)
        glPushMatrix(); 
        glScalef(r*1.8, r*0.15, r*0.10)
        glutSolidCube(1.0); glPopMatrix()
        glRotatef(90,0,0,1)
        glPushMatrix(); 
        glScalef(r*1.8, r*0.15, r*0.10); 
        glutSolidCube(1.0); 
        glPopMatrix()
        glPopMatrix()
        glPushMatrix(); 
        glTranslatef(0, r*0.75, r*0.10)
        glColor3f(0.10,0.85,1.00); 
        gluSphere(q, r*0.25, 14, 12); glPopMatrix()

    elif et == "brute":
        glPushMatrix()
        glTranslatef(0,0,r*0.9)
        glScalef(1.4,1.1,1.5)
        glColor3f(0.55,0.25,0.85)
        glutSolidCube(r*1.4)
        glPopMatrix()

        for sgn in (-1,1):
            glPushMatrix()
            glTranslatef(sgn*r*0.9,0,r*1.65)
            glRotatef(90,0,1,0)
            glColor3f(1.0,0.6,0.1)
            gluCylinder(q, r*0.28, r*0.28, r*0.45,14,1)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0,0,r*2.2)
        glColor3f(0.95,0.30,0.35)
        gluSphere(q, r*0.55,16,12)
        glPopMatrix()

        for sgn in (-1,1):
            glPushMatrix()
            glTranslatef(sgn*r*0.35, r*0.05, r*2.45)
            glRotatef(40,1,0,0)
            glRotatef(18*sgn,0,1,0)
            glColor3f(0.90,0.90,0.95)
            gluCylinder(q, r*0.08, r*0.08, r*0.40,10,1)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0,0,r*1.1)
        glScalef(1.5,0.2,0.2)
        glColor3f(0.10,0.10,0.12)
        glutSolidCube(r*1.4)
        glPopMatrix()

    else:
        glColor3f(0.20,0.95,0.35)
        gluSphere(q, r*0.95, 16, 14)
        glPushMatrix()
        glTranslatef(0, r*0.75, r*0.25)
        glScalef(r*0.9, r*0.20, r*0.35)
        glColor3f(0.05,0.20,0.90)
        glutSolidCube(1.0)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, -r*0.85, r*0.2)
        glScalef(r*0.7, r*0.4, r*0.6)
        glColor3f(0.10,0.10,0.12)
        glutSolidCube(1.0)
        glPopMatrix()

        for sgn in (-1,1):
            glPushMatrix()
            glTranslatef(sgn*r*0.75, 0, r*0.60)
            glRotatef(-90,1,0,0)
            glColor3f(0.98,0.55,0.10)
            gluCylinder(q, r*0.12, r*0.12, r*0.5,12,1)
            glPopMatrix()

        for sgn in (-1,1):
            glPushMatrix()
            glTranslatef(sgn*r*0.45, 0, -r*0.10)
            glRotatef(-90,1,0,0)
            glColor3f(0.98,0.55,0.10)
            gluCylinder(q, r*0.14, r*0.14, r*0.6,12,1)
            glPopMatrix()

    glPopMatrix()
    glDisable(GL_DEPTH_TEST)
    top_z = e["z"] + e["r"]*2.4
    draw_lifebar_world(e["x"], e["y"], top_z, e["hp"]/e["maxhp"], w=50.0, h=10.0)
    glEnable(GL_DEPTH_TEST)

## Bullets, Rockets, Grenades, pickups
def draw_bullet(b):
    if not b["alive"]:
        return
    glPushMatrix()
    glTranslatef(b["x"], b["y"], b["z"])
    glColor3f(1.0,1.0,0.2)
    glutSolidCube(8)
    glPopMatrix()

def draw_rocket(r):
    if not r["alive"]:
        return
    glPushMatrix()
    glTranslatef(r["x"], r["y"], r["z"])
    glColor3f(0.9, 0.5, 0.1)
    gluSphere(gluNewQuadric(), 10, 10, 8)
    glPopMatrix()

def draw_grenade(g):
    if not g["alive"]:
        return
    glPushMatrix()
    glTranslatef(g["x"], g["y"], g["z"])
    q = gluNewQuadric()
    glColor3f(0.16, 0.35, 0.16)
    gluSphere(q, 12, 18, 14)
    glPushMatrix()
    glTranslatef(0.0, 0.0, -1.1)
    glColor3f(0.25, 0.55, 0.25)
    gluCylinder(q, 12.4, 12.4, 2.2, 24, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, 0.0, 10.0)
    glColor3f(0.45, 0.45, 0.45)
    gluCylinder(q, 3.2, 3.2, 6.0, 12, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(4.0, -2.0, 12.0)
    glColor3f(0.75, 0.75, 0.75)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    gluCylinder(q, 0.7, 0.7, 3.6, 8, 1)
    glPopMatrix()
    glPushMatrix()
    glRotatef(90, 1, 0, 0)
    gluCylinder(q, 0.7, 0.7, 3.6, 8, 1)
    glPopMatrix()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(6.0, 0.0, 11.0)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.70, 0.70, 0.70)
    gluCylinder(q, 0.7, 0.7, 4.5, 8, 1)
    glPopMatrix()
    glPopMatrix()

# pickups
def draw_floor_pistol():
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, 0.6)
    glScalef(1.2, 1.2, 0.12)
    glColor3f(0.25, 0.60, 1.00)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 5)
    glScalef(0.9, 0.35, 0.35)
    glColor3f(0.18, 0.18, 0.20)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(10, 0, 6)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.35, 0.35, 0.40)
    gluCylinder(q, 1.4, 1.4, 8.0, 12, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-4, -4, 2)
    glRotatef(-25, 0, 0, 1)
    glScalef(0.35, 0.6, 0.35)
    glColor3f(0.25, 0.60, 1.00)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 14)
    glColor3f(0.25, 0.60, 1.00)
    gluSphere(q, 2.2, 12, 10)
    glPopMatrix()

def draw_floor_rifle():
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, 0.6)
    glScalef(1.4, 1.4, 0.12)
    glColor3f(0.20, 0.85, 0.30)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 6)
    glScalef(1.8, 0.35, 0.35)
    glColor3f(0.10, 0.10, 0.12)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(20, 0, 6)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.45, 0.45, 0.50)
    gluCylinder(q, 1.6, 1.6, 16.0, 14, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-16, -1.5, 6)
    glScalef(0.7, 0.35, 0.35)
    glColor3f(0.20, 0.85, 0.30)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(3, -4, 4)
    glRotatef(18, 0, 0, 1)
    glScalef(0.4, 0.6, 0.3)
    glColor3f(0.22, 0.22, 0.26)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 14)
    glColor3f(0.20, 0.85, 0.30)
    gluSphere(q, 2.2, 12, 10)
    glPopMatrix()

def draw_floor_machine_gun():
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, 0.6)
    glScalef(1.5, 1.5, 0.12)
    glColor3f(1.00, 0.80, 0.20)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 6)
    glScalef(1.6, 0.45, 0.45)
    glColor3f(0.10, 0.10, 0.11)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(18, 0, 6)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.55, 0.55, 0.58)
    gluCylinder(q, 2.4, 2.4, 18.0, 14, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-4, -5, 6)
    glColor3f(1.00, 0.60, 0.10)
    gluSphere(q, 3.2, 12, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 14)
    glColor3f(1.00, 0.80, 0.20)
    gluSphere(q, 2.2, 12, 10)
    glPopMatrix()

def draw_floor_rocket_launcher():
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, 0.6)
    glScalef(1.6, 1.6, 0.12)
    glColor3f(1.00, 0.30, 0.30)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 7)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.18, 0.32, 0.18)
    gluCylinder(q, 4.0, 4.0, 32.0, 16, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(16, 0, 7)
    glRotatef(90, 0, 1, 0)
    glColor3f(1.00, 0.30, 0.30)
    gluCylinder(q, 4.6, 4.6, 2.4, 12, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-16, 0, 7)
    glColor3f(0.30, 0.30, 0.32)
    gluSphere(q, 4.2, 14, 12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-2, -4.5, 4.5)
    glRotatef(-20, 0, 0, 1)
    glScalef(0.4, 0.8, 0.4)
    glColor3f(0.12, 0.12, 0.14)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 14)
    glColor3f(1.00, 0.30, 0.30)
    gluSphere(q, 2.2, 12, 10)
    glPopMatrix()

def draw_floor_health():
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, 0.6)
    glScalef(1.5, 1.5, 0.12)
    glColor3f(0.08, 0.95, 0.35)
    glutSolidCube(22)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 8.0)
    glScalef(1.6, 1.0, 0.6)
    glColor3f(0.95, 0.97, 1.00)
    glutSolidCube(16)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 12.0)
    glScalef(1.0, 0.20, 0.18)
    glColor3f(0.92, 0.10, 0.15)
    glutSolidCube(16)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 12.0)
    glScalef(0.20, 1.0, 0.18)
    glColor3f(0.92, 0.10, 0.15)
    glutSolidCube(16)
    glPopMatrix()

def draw_floor_ammo():
    q = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, 0.6)
    glScalef(1.6, 1.6, 0.12)
    glColor3f(1.00, 0.85, 0.15)
    glutSolidCube(22)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 8.0)
    glScalef(1.8, 1.1, 0.8)
    glColor3f(0.23, 0.38, 0.20)
    glutSolidCube(16)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 8.0)
    glScalef(1.9, 0.22, 0.82)
    glColor3f(1.00, 0.80, 0.10)
    glutSolidCube(16)
    glPopMatrix()
    for ix in (-5.0, 0.0, 5.0):
        glPushMatrix()
        glTranslatef(ix, 0.0, 13.0)
        glColor3f(0.93, 0.78, 0.18)
        gluCylinder(q, 1.6, 1.6, 7.0, 12, 1)
        glTranslatef(0.0, 0.0, 7.0)
        glColor3f(0.75, 0.38, 0.12)
        gluSphere(q, 1.9, 10, 8)
        glPopMatrix()

def draw_pickup(p):
    glPushMatrix()
    local_phase = pickup_bob_phase + (p["x"] + p["y"]) * 0.005
    bob = PICKUP_BOB_AMPLITUDE * math.sin(local_phase * 2.0)
    spin_deg = (local_phase * 90.0) % 360.0
    glTranslatef(p["x"], p["y"], p["z"] + 70 + bob)
    glRotatef(spin_deg, 0, 0, 1)
    t = p["type"]
    if t == "pistol":  draw_floor_pistol()
    elif t == "rifle": draw_floor_rifle()
    elif t == "machine_gun": draw_floor_machine_gun()
    elif t == "rocket": draw_floor_rocket_launcher()
    else:
        if t == "ammo":   draw_floor_ammo()
        elif t == "health": draw_floor_health()
        else:
            glColor3f(0.3, 0.7, 1.0)
            glutSolidCube(20)
    glPopMatrix()

## Draw Explosions
def draw_explosions():
    if not explosions:
        return
    q = gluNewQuadric()
    for ex in explosions:
        u = max(0.0, min(1.0, ex["t"] / ex["ttl"]))
        R = ex["r0"] + (ex["r1"] - ex["r0"]) * u
        core_r = max(12.0, R * 0.30)
        hot  = (1.00, 0.90, 0.20)
        cool = (0.40, 0.35, 0.35)
        cr = hot[0]*(1.0-u) + cool[0]*u
        cg = hot[1]*(1.0-u) + cool[1]*u
        cb = hot[2]*(1.0-u) + cool[2]*u
        glPushMatrix()
        glTranslatef(ex["x"], ex["y"], ex["z"] + 10.0 + 40.0*u)
        glColor3f(cr, cg, cb)
        gluSphere(q, core_r, 18, 14)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(ex["x"], ex["y"], ex["z"] + 6.0 + 30.0*u)
        glColor3f(0.95*(1.0-u) + 0.30*u, 0.35*(1.0-u) + 0.10*u, 0.08)
        gluSphere(q, max(core_r*1.25, R*0.45), 14, 12)
        glPopMatrix()
        ring_h = 3.0
        for k, scale in enumerate((0.7, 1.0, 1.3)):
            ring_r = max(10.0, R * 0.50 * scale)
            glPushMatrix()
            glTranslatef(ex["x"], ex["y"], ex["z"] + 0.5)
            if k == 0:   glColor3f(1.00, 0.45, 0.12)
            elif k == 1: glColor3f(0.90, 0.30, 0.10)
            else:        glColor3f(0.65, 0.18, 0.08)
            gluCylinder(q, ring_r, ring_r, ring_h, 32, 1)
            glPopMatrix()
        debris_s = max(1.5, 6.0*(1.0-u))
        for ang in (0.0, math.pi*0.5, math.pi, math.pi*1.5):
            dx, dy = math.cos(ang), math.sin(ang)
            px = ex["x"] + dx * (R * 0.6)
            py = ex["y"] + dy * (R * 0.6)
            pz = ex["z"] + 20.0 + 60.0 * (1.0 - u)
            glPushMatrix()
            glTranslatef(px, py, pz)
            glScalef(debris_s, debris_s, debris_s)
            glColor3f(0.55, 0.48, 0.42)
            glutSolidCube(1.0)
            glPopMatrix()

#### Draw Laser and Scope ####
def show_scope_overlay():
    if not scope_active:
        return
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW);  glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    cx, cy = WINDOW_W // 2, WINDOW_H // 2
    r = int(min(WINDOW_W, WINDOW_H) * (0.18 if first_person else 0.22))
    SEG = 64
    glColor3f(0.95, 0.95, 0.95)
    glBegin(GL_LINE_LOOP)
    for i in range(SEG):
        ang = 2.0 * math.pi * i / SEG
        glVertex2f(cx + r * math.cos(ang), cy + r * math.sin(ang))
    glEnd()
    tick = 16
    glBegin(GL_LINES)
    glVertex2f(cx - r, cy)
    glVertex2f(cx - r + tick, cy)
    glVertex2f(cx + r - tick, cy)
    glVertex2f(cx + r, cy)
    glVertex2f(cx, cy - r)
    glVertex2f(cx, cy - r + tick)
    glVertex2f(cx, cy + r - tick)
    glVertex2f(cx, cy + r)
    glEnd()
    s = 4
    glColor3f(1.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(cx - s, cy - s)
    glVertex2f(cx + s, cy - s)
    glVertex2f(cx + s, cy + s)
    glVertex2f(cx - s, cy + s)
    glEnd()
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_laser_sweep():
    if not laser_active:
        return
    u = max(0.0, min(1.0, laser_t / LASER_SWEEP_TIME))
    x = -GRID_LENGTH + (2.0 * GRID_LENGTH) * u
    glDisable(GL_DEPTH_TEST)
    glPushMatrix()
    glTranslatef(x, 0.0, 8.0)
    glScalef(LASER_THICKNESS, GRID_LENGTH * 2.2, 6.0)
    glColor3f(1.00, 0.10, 0.10)
    glutSolidCube(1.0)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(x, 0.0, 9.5)
    glScalef(LASER_GLOW_THICKNESS * 0.5, GRID_LENGTH * 2.2, 3.5)
    glColor3f(1.00, 0.55, 0.08)
    glutSolidCube(1.0)
    glPopMatrix()
    glEnable(GL_DEPTH_TEST)

def laser_positions():
    minX = -GRID_LENGTH + 80.0
    maxX =  GRID_LENGTH - 80.0
    u = max(0.0, min(1.0, laser_t / LASER_SWEEP_TIME))
    xL = minX + (maxX - minX) * u
    xR = minX + (maxX - minX) * u
    return xL, xR

def laser_kill():
    global health
    if game_over or not laser_active:
        return
    ground_here = ground_height_at(player_pos[0], player_pos[1])
    on_rock = ground_here > (GROUND_BASE_Z + 1.0)
    feet_on_ground = (abs(player_pos[2] - ground_here) < 2.0) and player_on_ground
    if on_rock or not feet_on_ground:
        return
    half_bar = LASER_THICKNESS * 0.5
    px = player_pos[0]
    xL, xR = laser_positions()
    touch = (abs(px - xL) <= (half_bar)) or (abs(px - xR) <= (half_bar))
    if touch:
        health = 0
        end_game()

#### Camera Setup ####
def setupCamera():
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    fov = fovY_default
    if scope_active: fov = fovY_zoom if first_person else fovY_zoom_3p
    gluPerspective(fov, ASPECT, 0.1, 4000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person:
        fx, fy = forward_vec(player_angle)
        rx, ry = fy, -fx
        eye_x = player_pos[0] + fx * 50 + rx * 3
        eye_y = player_pos[1] + fy * 50 + ry * 3
        eye_z = player_pos[2] + 100
        center_x = eye_x + fx * 600
        center_y = eye_y + fy * 600
        center_z = eye_z
        gluLookAt(eye_x, eye_y, eye_z, center_x, center_y, center_z, 0, 0, 1)
    else:
        gluLookAt(cam_x, cam_y, cam_z,
                  player_pos[0], player_pos[1], player_pos[2] + 110,
                  0, 0, 1)

































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