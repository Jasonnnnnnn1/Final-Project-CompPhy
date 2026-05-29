"""Ghost-ball aiming aid (8 Ball Pool style).

Shows where the cue ball must be at contact, the object-ball path through
the pocket aim, and the cue-ball deflection after impact.
Spacing uses 2 * BALL_RADIUS from constants.py.
"""

import math
import pygame
import constants as c

LINE_COLOR = (255, 255, 255)
LINE_WIDTH = 2
GHOST_RING_WIDTH = 2


def _ray_hits_ball(cue_pos, aim_dir, ball, contact_sep):
    """Return distance along aim_dir to contact, or None if no hit."""
    fc = pygame.Vector2(cue_pos.x - ball.x, cue_pos.y - ball.y)
    b = 2.0 * fc.dot(aim_dir)
    c_val = fc.length_squared() - contact_sep * contact_sep
    disc = b * b - 4.0 * c_val
    if disc < 0:
        return None
    sqrt_disc = math.sqrt(disc)
    t = (-b - sqrt_disc) * 0.5
    if t > 1.0:
        return t
    t = (-b + sqrt_disc) * 0.5
    if t > 1.0:
        return t
    return None


def find_first_object_ball(cue_ball, balls, aim_dir):
    contact_sep = 2.0 * cue_ball.radius
    cue_pos = pygame.Vector2(cue_ball.x, cue_ball.y)
    best_ball = None
    best_t = float("inf")

    for ball in balls:
        if not ball.alive or ball.is_cue:
            continue
        t = _ray_hits_ball(cue_pos, aim_dir, ball, contact_sep)
        if t is not None and t < best_t:
            best_t = t
            best_ball = ball

    return best_ball


def compute_ghost_shot(cue_ball, object_ball, mouse_pos):
    """Place ghost one ball diameter from object, on the cue side (contact point)."""
    cue = pygame.Vector2(cue_ball.x, cue_ball.y)
    obj = pygame.Vector2(object_ball.x, object_ball.y)
    mouse = pygame.Vector2(mouse_pos)
    sep = 2.0 * cue_ball.radius

    approach = obj - cue
    if approach.length_squared() < sep * sep:
        return None

    to_mouse = mouse - obj
    # Mouse on the ball: treat as full-ball hit along cue approach
    if to_mouse.length_squared() < sep * sep:
        obj_dir = approach.normalize()
    else:
        obj_dir = to_mouse.normalize()
        # Object path is toward the mouse; ghost must stay on the cue side of object
        if obj_dir.dot(approach) < 0:
            obj_dir = -obj_dir

    ghost_pos = obj - obj_dir * sep

    # Contact point must sit between cue and object, not inside the object
    if (ghost_pos - obj).dot(approach) >= 0:
        return None
    if (ghost_pos - cue).length() >= (obj - cue).length():
        return None

    return {
        "ghost_pos": ghost_pos,
        "object_ball": object_ball,
        "object_dir": obj_dir,
    }


def _cue_deflection_dir(cue_pos, ghost_pos, obj_dir):
    """Tangent direction for cue ball after contact (equal-mass elastic)."""
    perp = pygame.Vector2(-obj_dir.y, obj_dir.x)
    if (cue_pos - ghost_pos).dot(perp) < 0:
        perp = -perp
    return perp.normalize()


def _line_clear(cue_ball, ghost_pos, balls, ignore_ball):
    start = pygame.Vector2(cue_ball.x, cue_ball.y)
    path = ghost_pos - start
    length = path.length()
    if length < 1.0:
        return True
    path_n = path / length
    min_pass = 2.0 * cue_ball.radius

    for ball in balls:
        if not ball.alive or ball.is_cue or ball is ignore_ball:
            continue
        center = pygame.Vector2(ball.x, ball.y)
        rel = center - start
        t = rel.dot(path_n)
        if t < 0 or t > length:
            continue
        perp = (rel - path_n * t).length()
        if perp < min_pass:
            return False
    return True


def get_ghost_aim(cue_ball, balls, mouse_pos, aim_dir):
    if aim_dir.length_squared() < 1e-6:
        return None

    aim_dir = aim_dir.normalize()
    target = find_first_object_ball(cue_ball, balls, aim_dir)
    if target is None:
        return None

    shot = compute_ghost_shot(cue_ball, target, mouse_pos)
    if shot is None:
        return None

    cue_pos = pygame.Vector2(cue_ball.x, cue_ball.y)
    to_ghost = shot["ghost_pos"] - cue_pos
    if to_ghost.length_squared() < 1.0:
        return None
    if to_ghost.normalize().dot(aim_dir) < 0.2:
        return None

    if not _line_clear(cue_ball, shot["ghost_pos"], balls, target):
        return None

    shot["cue_pos"] = cue_pos
    shot["cue_deflect_dir"] = _cue_deflection_dir(cue_pos, shot["ghost_pos"], shot["object_dir"])
    return shot


def draw_ghost_indicator(surface, cue_ball, balls, mouse_pos, aim_dir):
    """8 Ball Pool style: white ring ghost + three solid white guide lines."""
    shot = get_ghost_aim(cue_ball, balls, mouse_pos, aim_dir)
    if shot is None:
        return

    r = int(cue_ball.radius)
    cue_pos = shot["cue_pos"]
    ghost_pos = shot["ghost_pos"]
    obj = shot["object_ball"]
    obj_dir = shot["object_dir"]
    deflect_dir = shot["cue_deflect_dir"]

    cx, cy = int(cue_pos.x), int(cue_pos.y)
    gx, gy = int(ghost_pos.x), int(ghost_pos.y)
    ox, oy = int(obj.x), int(obj.y)

    obj_path_len = min(320, c.SCREEN_TABLE_W * 0.4)
    deflect_len = min(140, obj_path_len * 0.45)

    obj_end = ghost_pos + obj_dir * (obj_path_len + 2.0 * r)
    deflect_end = ghost_pos + deflect_dir * deflect_len

    # 1) Cue ball → ghost ball
    pygame.draw.line(surface, LINE_COLOR, (cx, cy), (gx, gy), LINE_WIDTH)

    # 2) Ghost → through object ball → aim direction
    pygame.draw.line(
        surface, LINE_COLOR,
        (gx, gy), (int(obj_end.x), int(obj_end.y)), LINE_WIDTH
    )

    # 3) Cue deflection (tangent from ghost ball)
    pygame.draw.line(
        surface, LINE_COLOR,
        (gx, gy), (int(deflect_end.x), int(deflect_end.y)), LINE_WIDTH
    )

    # Ghost ball ring (outline only)
    pygame.draw.circle(surface, LINE_COLOR, (gx, gy), r, GHOST_RING_WIDTH)
