import math
import sys
import pygame
import pymunk

# -----------------------------------------------------------------------------
# How Pymunk works (for your physics project):
# -----------------------------------------------------------------------------
# - Space: The "world" where simulation runs. Holds all bodies and shapes.
#   space.step(dt) advances time by dt (e.g. 1/60 s).
# - Body: A rigid body with mass, position, velocity. Dynamic bodies move.
#   body.position, body.velocity are (x, y) in pixels (we use pygame coords).
# - Shape: Attached to a body; defines collision (e.g. Circle). Has friction
#   and elasticity (restitution). Collisions are solved automatically.
# - Static body: space.static_body. Shapes attached to it don't move (e.g. walls).
# - We use gravity = (0, 0) so balls only move when hit (billiards).
# -----------------------------------------------------------------------------

# Basic 2D billiards-style simulator in pygame + pymunk
# Focus: momentum and kinetic energy; physics handled by pymunk (Chipmunk2D).

WIDTH, HEIGHT = 900, 500
TABLE_MARGIN = 50
FPS = 60

BG_COLOR = (20, 120, 40)       # table green
RAIL_COLOR = (10, 60, 20)
TEXT_COLOR = (240, 240, 240)

# Pymunk physics parameters
BALL_ELASTICITY = 0.9         # Ball-ball and ball-rail bounce (0–1)
BALL_FRICTION = 0.6           # Sliding/rolling friction on cloth
RAIL_FRICTION = 0.4           # Friction on cushions
SPACE_DAMPING = 0.4            # Slight velocity damping per second (rolling resistance)
MIN_SPEED = 15.0               # Below this speed we set velocity to zero

# Simple circular pockets (slightly inset from the rails so balls can reach them)
POCKET_RADIUS = 26
POCKET_POSITIONS = [
    (TABLE_MARGIN + 5, TABLE_MARGIN + 5),                        # top-left
    (WIDTH - TABLE_MARGIN - 5, TABLE_MARGIN + 5),                # top-right
    (TABLE_MARGIN + 5, HEIGHT - TABLE_MARGIN - 5),               # bottom-left
    (WIDTH - TABLE_MARGIN - 5, HEIGHT - TABLE_MARGIN - 5),       # bottom-right
    (WIDTH // 2, TABLE_MARGIN + 5),                              # top-middle
    (WIDTH // 2, HEIGHT - TABLE_MARGIN - 5),                     # bottom-middle
]


class Ball:
    """Ball with physics handled by pymunk. body/shape are None if pocketed."""

    def __init__(self, body, shape, radius, mass, color, is_cue=False):
        self.body = body
        self.shape = shape
        self.radius = radius
        self.mass = mass
        self.color = color
        self.is_cue = bool(is_cue)
        self.alive = True

    @property
    def x(self):
        return self.body.position.x if self.body else 0.0

    @property
    def y(self):
        return self.body.position.y if self.body else 0.0

    @property
    def vx(self):
        return self.body.velocity.x if self.body else 0.0

    @property
    def vy(self):
        return self.body.velocity.y if self.body else 0.0

    def position(self):
        return pygame.Vector2(self.x, self.y)

    def velocity(self):
        return pygame.Vector2(self.vx, self.vy)

    def set_velocity(self, v):
        if self.body:
            self.body.velocity = (float(v.x), float(v.y))

    def draw(self, surface):
        if self.alive and self.body:
            pos = self.body.position
            pygame.draw.circle(surface, self.color, (int(pos.x), int(pos.y)), self.radius)


def build_physics_space(ball_specs):
    """
    Create the pymunk Space with table walls and balls.
    ball_specs: list of (x, y, radius, mass, color, is_cue).
    Returns (space, list of Ball).
    """
    space = pymunk.Space()
    space.gravity = (0, 0)

    # Table boundaries (play area)
    left = TABLE_MARGIN
    right = WIDTH - TABLE_MARGIN
    top = TABLE_MARGIN
    bottom = HEIGHT - TABLE_MARGIN

    # Static walls (rails) - segments so balls bounce off
    static = space.static_body
    walls = [
        pymunk.Segment(static, (left, top), (right, top), 2),      # top
        pymunk.Segment(static, (right, top), (right, bottom), 2),  # right
        pymunk.Segment(static, (right, bottom), (left, bottom), 2), # bottom
        pymunk.Segment(static, (left, bottom), (left, top), 2),      # left
    ]
    for seg in walls:
        seg.elasticity = BALL_ELASTICITY
        seg.friction = RAIL_FRICTION
    space.add(*walls)

    # Balls
    balls = []
    for (x, y, radius, mass, color, is_cue) in ball_specs:
        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment)
        body.position = (x, y)
        shape = pymunk.Circle(body, radius)
        shape.elasticity = BALL_ELASTICITY
        shape.friction = BALL_FRICTION
        space.add(body, shape)
        balls.append(Ball(body, shape, radius, mass, color, is_cue))

    return space, balls


def compute_totals(balls):
    """Total linear momentum (Px, Py) and kinetic energy (KE)."""
    Px = Py = KE = 0.0
    for b in balls:
        if not b.alive or not b.body:
            continue
        Px += b.mass * b.vx
        Py += b.mass * b.vy
        KE += 0.5 * b.mass * (b.vx * b.vx + b.vy * b.vy)
    return Px, Py, KE


def draw_table(surface):
    surface.fill(RAIL_COLOR)
    pygame.draw.rect(
        surface,
        BG_COLOR,
        pygame.Rect(
            TABLE_MARGIN,
            TABLE_MARGIN,
            WIDTH - 2 * TABLE_MARGIN,
            HEIGHT - 2 * TABLE_MARGIN,
        ),
        border_radius=20,
    )

    # Draw pockets
    for (px, py) in POCKET_POSITIONS:
        pygame.draw.circle(surface, (0, 0, 0), (int(px), int(py)), POCKET_RADIUS)


def handle_pocketing(space, balls):
    """If a ball (non-cue) is inside a pocket, remove it from the simulation."""
    for b in balls:
        if not b.alive or not b.body or b.is_cue:
            continue
        x, y = b.body.position.x, b.body.position.y
        for (px, py) in POCKET_POSITIONS:
            if (x - px) ** 2 + (y - py) ** 2 <= POCKET_RADIUS ** 2:
                space.remove(b.shape, b.body)
                b.body = None
                b.shape = None
                b.alive = False
                break


def physics_step(space, balls, dt):
    """Advance pymunk simulation, apply damping, then check pocketing."""
    space.step(dt)
    # Rolling resistance: slow down velocities a bit each frame
    for b in balls:
        if not b.alive or not b.body:
            continue
        v = b.body.velocity
        speed = (v.x ** 2 + v.y ** 2) ** 0.5
        if speed < MIN_SPEED:
            b.body.velocity = (0, 0)
        elif speed > 0:
            scale = max(0, 1 - SPACE_DAMPING * dt)
            b.body.velocity = (v.x * scale, v.y * scale)
    handle_pocketing(space, balls)


def duplicate_space_for_prediction(balls, cue_velocity_override=None):
    """
    Build a copy of the physics space with same walls and ball positions/velocities.
    If cue_velocity_override is (vx, vy), the first ball gets that velocity.
    Returns (space, list of pymunk bodies in same order as balls).
    """
    space = pymunk.Space()
    space.gravity = (0, 0)
    left, right = TABLE_MARGIN, WIDTH - TABLE_MARGIN
    top, bottom = TABLE_MARGIN, HEIGHT - TABLE_MARGIN
    static = space.static_body
    walls = [
        pymunk.Segment(static, (left, top), (right, top), 2),
        pymunk.Segment(static, (right, top), (right, bottom), 2),
        pymunk.Segment(static, (right, bottom), (left, bottom), 2),
        pymunk.Segment(static, (left, bottom), (left, top), 2),
    ]
    for seg in walls:
        seg.elasticity = BALL_ELASTICITY
        seg.friction = RAIL_FRICTION
    space.add(*walls)

    body_list = []
    for i, b in enumerate(balls):
        if not b.alive:
            body_list.append(None)
            continue
        vx, vy = b.vx, b.vy
        if i == 0 and cue_velocity_override is not None:
            vx, vy = cue_velocity_override
        moment = pymunk.moment_for_circle(b.mass, 0, b.radius)
        body = pymunk.Body(b.mass, moment)
        body.position = (b.x, b.y)
        body.velocity = (vx, vy)
        shape = pymunk.Circle(body, b.radius)
        shape.elasticity = BALL_ELASTICITY
        shape.friction = BALL_FRICTION
        space.add(body, shape)
        body_list.append(body)
    return space, body_list


def step_prediction_space(space, body_list, balls, dt):
    """One step of the duplicate space + damping; remove pocketed from space."""
    space.step(dt)
    for i, body in enumerate(body_list):
        if body is None:
            continue
        v = body.velocity
        speed = (v.x ** 2 + v.y ** 2) ** 0.5
        if speed < MIN_SPEED:
            body.velocity = (0, 0)
        else:
            scale = max(0, 1 - SPACE_DAMPING * dt)
            body.velocity = (v.x * scale, v.y * scale)
    # Pocketing: remove body if in pocket (non-cue only)
    for i, body in enumerate(body_list):
        if body is None or i == 0:
            continue
        x, y = body.position.x, body.position.y
        for (px, py) in POCKET_POSITIONS:
            if (x - px) ** 2 + (y - py) ** 2 <= POCKET_RADIUS ** 2:
                try:
                    for s in body.shapes:
                        space.remove(s)
                    space.remove(body)
                except Exception:
                    pass
                body_list[i] = None
                break


def simulate_shot(balls, cue_index, target_index, angle_deg, speed):
    """Run pymunk simulation for a shot; return True if target is pocketed."""
    vel = (speed * math.cos(math.radians(angle_deg)), speed * math.sin(math.radians(angle_deg)))
    space, body_list = duplicate_space_for_prediction(balls, vel)
    dt = 1.0 / 180.0
    for _ in range(int(6.0 / dt)):
        step_prediction_space(space, body_list, balls, dt)
        if target_index < len(body_list) and body_list[target_index] is None:
            return True
    return False


def find_shot_to_pot(balls, cue_index=0, target_index=1):
    """Brute-force search for an angle that pockets the target ball."""
    speed = 500.0
    for angle_deg in range(0, 360, 3):
        if simulate_shot(balls, cue_index, target_index, angle_deg, speed):
            return angle_deg, speed
    return None, None

'''
def predict_trajectory(balls, cue_index, target_pos, shot_speed=400.0, max_steps=180):
    """
    Use a duplicate pymunk space to predict cue and object ball paths.
    Returns (cue_trajectory, hit_ball_index, object_trajectories).
    """
    if cue_index >= len(balls) or not balls[cue_index].alive:
        return [], None, {}
    cue = balls[cue_index]
    dx = target_pos[0] - cue.x
    dy = target_pos[1] - cue.y
    dist = math.hypot(dx, dy)
    if dist < 5.0:
        return [], None, {}
    dir_x = dx / dist
    dir_y = dy / dist
    vel = (dir_x * shot_speed, dir_y * shot_speed)

    space, body_list = duplicate_space_for_prediction(balls, vel)
    cue_trajectory = []
    hit_ball_index = None
    object_trajectories = {}
    dt = 1.0 / 90.0

    for step in range(max_steps):
        if body_list[0] is not None:
            p = body_list[0].position
            cue_trajectory.append((int(p.x), int(p.y)))
        step_prediction_space(space, body_list, balls, dt)
        if body_list[0] is None:
            break
        speed = (body_list[0].velocity.x ** 2 + body_list[0].velocity.y ** 2) ** 0.5
        if speed < MIN_SPEED:
            break
        # Detect first contact with another ball
        if hit_ball_index is None:
            for i in range(1, len(body_list)):
                if body_list[i] is not None:
                    d = (body_list[0].position.x - body_list[i].position.x) ** 2 + (
                        body_list[0].position.y - body_list[i].position.y
                    ) ** 2
                    if d < (balls[0].radius + balls[i].radius + 2) ** 2:
                        hit_ball_index = i
                        object_trajectories[i] = [(int(body_list[i].position.x), int(body_list[i].position.y))]
                        break
        else:
            if hit_ball_index < len(body_list) and body_list[hit_ball_index] is not None:
                p = body_list[hit_ball_index].position
                object_trajectories[hit_ball_index].append((int(p.x), int(p.y)))

    return cue_trajectory, hit_ball_index, object_trajectories
'''

def main():
    pygame.init()
    pygame.display.set_caption("Computational Physics: Billiards & Momentum (Pymunk)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    # Ball layout: (x, y, radius, mass, color, is_cue)
    ball_radius = 15
    ball_specs = [
        (WIDTH * 0.25, HEIGHT * 0.5, ball_radius, 1.0, (250, 240, 240), True),
        (WIDTH * 0.55, HEIGHT * 0.45, ball_radius, 1.0, (240, 200, 80), False),
        (WIDTH * 0.55, HEIGHT * 0.55, ball_radius, 1.0, (80, 160, 240), False),
        (WIDTH * 0.7, HEIGHT * 0.5, ball_radius, 1.0, (200, 100, 150), False),
    ]
    space, balls = build_physics_space(ball_specs)

    shot_message = "Move mouse to aim, click to shoot, SPACE for auto-shot"
    shot_power = 400.0  # Adjustable shot power (speed)
    MIN_SHOT_POWER = 200.0
    MAX_SHOT_POWER = 800.0

    running = True
    aiming = True
    while running:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0  # seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    angle_deg, speed = find_shot_to_pot(balls)
                    if angle_deg is not None and balls[0].body:
                        theta = math.radians(angle_deg)
                        balls[0].body.velocity = (speed * math.cos(theta), speed * math.sin(theta))
                        shot_message = f"Shot: angle={angle_deg}°, speed={speed:.0f}"
                        aiming = False
                    else:
                        shot_message = "No simple direct shot found"
                elif event.key == pygame.K_r:
                    if balls[0].body:
                        balls[0].body.velocity = (0, 0)
                    aiming = True
                    shot_message = "Aiming reset"
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # Increase shot power
                    shot_power = min(shot_power + 50.0, MAX_SHOT_POWER)
                    shot_message = f"Shot power: {shot_power:.0f}"
                elif event.key == pygame.K_MINUS:
                    # Decrease shot power
                    shot_power = max(shot_power - 50.0, MIN_SHOT_POWER)
                    shot_message = f"Shot power: {shot_power:.0f}"
            elif event.type == pygame.MOUSEWHEEL:
                # Adjust shot power with mouse wheel
                if event.y > 0:
                    shot_power = min(shot_power + 30.0, MAX_SHOT_POWER)
                else:
                    shot_power = max(shot_power - 30.0, MIN_SHOT_POWER)
                shot_message = f"Shot power: {shot_power:.0f}"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not balls[0].alive or not balls[0].body:
                    pass
                else:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    dx = mouse_x - balls[0].x
                    dy = mouse_y - balls[0].y
                    dist = math.hypot(dx, dy)
                    if dist > 5.0:
                        dir_x = dx / dist
                        dir_y = dy / dist
                        balls[0].body.velocity = (dir_x * shot_power, dir_y * shot_power)
                        aiming = False
                        shot_message = f"Manual shot: speed={shot_power:.0f}"

        # Update physics (pymunk step + damping + pocketing)
        physics_step(space, balls, dt)

        # Compute totals for display
        Px, Py, KE = compute_totals(balls)

        # Draw
        draw_table(screen)
        for ball in balls:
            if ball.alive:
                ball.draw(screen)

        # Draw aiming arrow and trajectory preview when cue is at rest
        cue = balls[0]
        if aiming and cue.alive and cue.body:
            if (cue.vx ** 2 + cue.vy ** 2) ** 0.5 < MIN_SPEED:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                start = (int(cue.x), int(cue.y))
                
                '''
                # Draw trajectory preview with current shot power
                cue_trajectory, hit_ball_idx, object_trajectories = predict_trajectory(balls, 0, (mouse_x, mouse_y), shot_power)
                
                # Draw cue ball trajectory (yellow/white)
                if len(cue_trajectory) > 1:
                    # Draw trajectory path as a smooth line
                    for i in range(len(cue_trajectory) - 1):
                        pygame.draw.line(screen, (255, 255, 200), cue_trajectory[i], cue_trajectory[i+1], 2)
                    # Draw dots along the path
                    for i in range(0, len(cue_trajectory), 10):
                        pygame.draw.circle(screen, (255, 255, 200), cue_trajectory[i], 3)
                
                # Draw object ball trajectories with simple arrows (cyan/blue)
                for obj_idx, obj_traj in object_trajectories.items():
                    if obj_idx < len(balls) and len(obj_traj) > 1:
                        obj_ball = balls[obj_idx]
                        # Draw trajectory line
                        for i in range(len(obj_traj) - 1):
                            pygame.draw.line(screen, (100, 200, 255), obj_traj[i], obj_traj[i+1], 2)
                        
                        # Draw simple arrows at regular intervals - cleaner and less warped
                        arrow_spacing = 20  # Space between arrows
                        for i in range(arrow_spacing, len(obj_traj) - 5, arrow_spacing):
                            if i < len(obj_traj) - 1:
                                # Get direction from a few points ahead for smoother arrow direction
                                look_ahead = min(5, len(obj_traj) - i - 1)
                                p1 = obj_traj[i]
                                p2 = obj_traj[i + look_ahead]
                                dx = p2[0] - p1[0]
                                dy = p2[1] - p1[1]
                                dist = math.hypot(dx, dy)
                                if dist > 0.1:
                                    # Simple arrow: just a small triangle pointing forward
                                    angle = math.atan2(dy, dx)
                                    arrow_size = 8
                                    # Arrow tip at p2
                                    tip = p2
                                    # Arrow base points
                                    base1 = (
                                        int(p2[0] - arrow_size * math.cos(angle - 2.5)),
                                        int(p2[1] - arrow_size * math.sin(angle - 2.5))
                                    )
                                    base2 = (
                                        int(p2[0] - arrow_size * math.cos(angle + 2.5)),
                                        int(p2[1] - arrow_size * math.sin(angle + 2.5))
                                    )
                                    pygame.draw.polygon(screen, (100, 200, 255), [tip, base1, base2])
                    
                    # Highlight the object ball that would be hit
                    if obj_idx < len(balls):
                        hit_ball = balls[obj_idx]
                        if hit_ball.alive:
                            # Draw a circle around the ball that would be hit
                            pygame.draw.circle(screen, (255, 200, 0), 
                                             (int(hit_ball.x), int(hit_ball.y)), 
                                             hit_ball.radius + 5, 3)
                '''
                
                # Draw aiming arrow
                end_vec = pygame.Vector2(mouse_x - cue.x, mouse_y - cue.y)
                if end_vec.length() > 0:
                    # Limit arrow length for clarity
                    max_arrow_len = 160
                    if end_vec.length() > max_arrow_len:
                        end_vec.scale_to_length(max_arrow_len)
                    end = (int(cue.x + end_vec.x), int(cue.y + end_vec.y))
                    pygame.draw.line(screen, (255, 255, 255), start, end, 3)
                    # Simple arrowhead
                    head_size = 10
                    angle = math.atan2(end_vec.y, end_vec.x)
                    left = (
                        int(end[0] - head_size * math.cos(angle - math.pi / 6)),
                        int(end[1] - head_size * math.sin(angle - math.pi / 6)),
                    )
                    right = (
                        int(end[0] - head_size * math.cos(angle + math.pi / 6)),
                        int(end[1] - head_size * math.sin(angle + math.pi / 6)),
                    )
                    pygame.draw.polygon(screen, (255, 255, 255), [end, left, right])

        # Momentum and energy text
        text_lines = [
            f"Total Px: {Px:7.2f}",
            f"Total Py: {Py:7.2f}",
            f"Total KE: {KE:7.2f}",
            f"Shot Power: {shot_power:.0f} (+/- or mouse wheel)",
            "ESC to quit, R to reset aim",
            shot_message,
        ]
        for idx, line in enumerate(text_lines):
            surf = font.render(line, True, TEXT_COLOR)
            screen.blit(surf, (20, 15 + idx * 22))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()


