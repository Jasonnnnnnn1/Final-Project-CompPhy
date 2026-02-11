import math
import sys
import pygame


# Basic 2D billiards-style simulator in pygame
# Focus: momentum and kinetic energy conservation in elastic collisions.

WIDTH, HEIGHT = 900, 500
TABLE_MARGIN = 50
FPS = 60

BG_COLOR = (20, 120, 40)       # table green
RAIL_COLOR = (10, 60, 20)
TEXT_COLOR = (240, 240, 240)

# Damping / realism parameters - balanced for good gameplay
BALL_RESTITUTION = 0.88       # Slight energy loss on ball-ball collisions
RAIL_RESTITUTION = 0.85       # Rails absorb some energy
FRICTION_LINEAR = 120.0       # Moderate rolling friction
FRICTION_QUAD = 0.12          # Speed-dependent drag
MIN_SPEED_THRESHOLD = 8.0     # Below this speed, ball stops (prevents tiny movements)

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
    def __init__(
        self,
        x,
        y,
        vx,
        vy,
        radius=20,
        mass=1.0,
        color=(220, 220, 220),
        is_cue=False,
    ):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = radius
        self.mass = float(mass)
        self.color = color
        self.is_cue = bool(is_cue)
        self.alive = True

    def position(self):
        return pygame.Vector2(self.x, self.y)

    def velocity(self):
        return pygame.Vector2(self.vx, self.vy)

    def set_velocity(self, v):
        self.vx, self.vy = float(v.x), float(v.y)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)


def handle_wall_collisions(ball: Ball):
    left = TABLE_MARGIN
    right = WIDTH - TABLE_MARGIN
    top = TABLE_MARGIN
    bottom = HEIGHT - TABLE_MARGIN

    # Left/right rails
    if ball.x - ball.radius < left:
        ball.x = left + ball.radius
        ball.vx *= -RAIL_RESTITUTION
    elif ball.x + ball.radius > right:
        ball.x = right - ball.radius
        ball.vx *= -RAIL_RESTITUTION

    # Top/bottom rails
    if ball.y - ball.radius < top:
        ball.y = top + ball.radius
        ball.vy *= -RAIL_RESTITUTION
    elif ball.y + ball.radius > bottom:
        ball.y = bottom - ball.radius
        ball.vy *= -RAIL_RESTITUTION


def resolve_ball_collision(b1: Ball, b2: Ball, restitution: float = 1.0):
    """
    Resolve an elastic collision between two balls using conservation
    of momentum and kinetic energy (via impulse method).
    """
    p1 = b1.position()
    p2 = b2.position()
    v1 = b1.velocity()
    v2 = b2.velocity()

    n = p1 - p2
    dist = n.length()
    min_dist = b1.radius + b2.radius

    if dist == 0:
        # Avoid division by zero: nudge slightly
        n = pygame.Vector2(1.0, 0.0)
        dist = 1.0

    # Check overlap (collision)
    if dist >= min_dist:
        return

    # Normal unit vector from 2 to 1
    n_hat = n / dist

    # Relative velocity along the normal
    rel_vel = (v1 - v2).dot(n_hat)

    # If balls are separating, don't resolve
    if rel_vel > 0:
        return

    m1 = b1.mass
    m2 = b2.mass

    # Impulse scalar for 1D collision along n_hat
    j = -(1.0 + restitution) * rel_vel / (1.0 / m1 + 1.0 / m2)

    # Apply impulse
    v1_post = v1 + (j / m1) * n_hat
    v2_post = v2 - (j / m2) * n_hat

    b1.set_velocity(v1_post)
    b2.set_velocity(v2_post)

    # Positional correction: separate the balls so they don't remain overlapped
    penetration = min_dist - dist
    if penetration > 0:
        # Move balls proportional to inverse mass (heavier moves less)
        total_inv_mass = (1.0 / m1) + (1.0 / m2)
        if total_inv_mass == 0:
            return
        correction = penetration / total_inv_mass
        b1_shift = correction * (1.0 / m1) * n_hat
        b2_shift = correction * (1.0 / m2) * -n_hat

        b1.x += b1_shift.x
        b1.y += b1_shift.y
        b2.x += b2_shift.x
        b2.y += b2_shift.y


def compute_totals(balls):
    """
    Compute total linear momentum and kinetic energy of the system.
    Returns (Px, Py, KE).
    """
    Px = 0.0
    Py = 0.0
    KE = 0.0
    for b in balls:
        if not b.alive:
            continue
        Px += b.mass * b.vx
        Py += b.mass * b.vy
        speed2 = b.vx * b.vx + b.vy * b.vy
        KE += 0.5 * b.mass * speed2
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


def handle_pocketing(balls):
    """
    Mark balls as pocketed (not alive) if they reach any pocket.
    For now we do not pocket the cue ball, so you can always shoot again.
    """
    for b in balls:
        if not b.alive:
            continue
        if b.is_cue:
            continue
        for (px, py) in POCKET_POSITIONS:
            dx = b.x - px
            dy = b.y - py
            if dx * dx + dy * dy <= POCKET_RADIUS * POCKET_RADIUS:
                b.alive = False
                b.vx = 0.0
                b.vy = 0.0
                break


def physics_step(balls, dt):
    # Update positions and handle wall collisions (with friction and damping)
    for ball in balls:
        if not ball.alive:
            continue
        ball.update(dt)
        handle_wall_collisions(ball)

        # Apply strong rolling friction - real billiards balls slow down quickly
        speed = math.hypot(ball.vx, ball.vy)
        if speed > 0.0:
            # Very strong deceleration that grows with speed
            decel = FRICTION_LINEAR + FRICTION_QUAD * speed
            dv = decel * dt
            if dv >= speed or speed < MIN_SPEED_THRESHOLD:
                # Stop the ball if it's moving too slowly (realistic)
                ball.vx = 0.0
                ball.vy = 0.0
            else:
                scale = (speed - dv) / speed
                ball.vx *= scale
                ball.vy *= scale

    # Handle ball-ball collisions (pairwise) - these lose significant energy
    n_balls = len(balls)
    for i in range(n_balls):
        for j in range(i + 1, n_balls):
            if not balls[i].alive or not balls[j].alive:
                continue
            resolve_ball_collision(balls[i], balls[j], restitution=BALL_RESTITUTION)

    # Handle pocketing
    handle_pocketing(balls)


def physics_step_ideal(balls, dt):
    """
    Simpler, nearly ideal physics (no friction, perfectly elastic)
    used only for planning the \"best\" shot in the search.
    """
    # Update positions and handle wall collisions (perfectly elastic)
    left = TABLE_MARGIN
    right = WIDTH - TABLE_MARGIN
    top = TABLE_MARGIN
    bottom = HEIGHT - TABLE_MARGIN

    for ball in balls:
        if not ball.alive:
            continue
        ball.update(dt)

        if ball.x - ball.radius < left:
            ball.x = left + ball.radius
            ball.vx *= -1.0
        elif ball.x + ball.radius > right:
            ball.x = right - ball.radius
            ball.vx *= -1.0

        if ball.y - ball.radius < top:
            ball.y = top + ball.radius
            ball.vy *= -1.0
        elif ball.y + ball.radius > bottom:
            ball.y = bottom - ball.radius
            ball.vy *= -1.0

    # Handle ball-ball collisions with perfectly elastic response
    n_balls = len(balls)
    for i in range(n_balls):
        for j in range(i + 1, n_balls):
            if not balls[i].alive or not balls[j].alive:
                continue
            resolve_ball_collision(balls[i], balls[j], restitution=1.0)

    # Handle pocketing
    handle_pocketing(balls)


def clone_balls(balls):
    clones = []
    for b in balls:
        clone = Ball(
            x=b.x,
            y=b.y,
            vx=b.vx,
            vy=b.vy,
            radius=b.radius,
            mass=b.mass,
            color=b.color,
            is_cue=b.is_cue,
        )
        clone.alive = b.alive
        clones.append(clone)
    return clones


def simulate_shot(balls, cue_index, target_index, angle_deg, speed):
    """
    Run a short off-screen simulation for a given shot and
    return True if the target ball ends up in any pocket.
    """
    sim_balls = clone_balls(balls)

    cue = sim_balls[cue_index]
    if not cue.alive:
        return False

    theta = math.radians(angle_deg)
    cue.vx = speed * math.cos(theta)
    cue.vy = speed * math.sin(theta)

    t_max = 6.0  # seconds (allow a bit more time to reach a pocket)
    dt = 1.0 / 300.0
    steps = int(t_max / dt)

    for _ in range(steps):
        physics_step_ideal(sim_balls, dt)
        target = sim_balls[target_index]
        if not target.alive:
            # Target has been pocketed
            return True

    return False


def find_shot_to_pot(balls, cue_index=0, target_index=1):
    """
    Brute-force search over shot angles to find a direction that
    pockets the target ball, using the same physics as the main sim.
    """
    # Fixed shot speed (you can tune this)
    speed = 500.0

    # Try angles around the full circle, coarse step to keep it fast
    for angle_deg in range(0, 360, 2):
        if simulate_shot(balls, cue_index, target_index, angle_deg, speed):
            return angle_deg, speed

    return None, None


def predict_trajectory(balls, cue_index, target_pos, shot_speed=400.0, max_steps=200):
    """
    Simulate the cue ball's trajectory when shot toward target_pos.
    Returns:
    - cue_trajectory: list of (x, y) positions for cue ball
    - hit_ball_index: which ball the cue ball hits first (if any)
    - object_trajectories: dict mapping ball_index -> list of (x, y) positions for object balls after collision
    """
    if cue_index >= len(balls) or not balls[cue_index].alive:
        return [], None, {}
    
    cue = balls[cue_index]
    
    # Calculate shot direction
    dx = target_pos[0] - cue.x
    dy = target_pos[1] - cue.y
    dist = math.hypot(dx, dy)
    if dist < 5.0:
        return [], None, {}
    
    dir_x = dx / dist
    dir_y = dy / dist
    
    # Clone balls for simulation
    sim_balls = clone_balls(balls)
    sim_cue = sim_balls[cue_index]
    sim_cue.vx = dir_x * shot_speed
    sim_cue.vy = dir_y * shot_speed
    
    cue_trajectory = [(int(sim_cue.x), int(sim_cue.y))]
    hit_ball_index = None
    object_trajectories = {}  # Track trajectories of object balls after they're hit
    dt = 1.0 / 120.0  # Smaller dt for smoother trajectory
    
    for step in range(max_steps):
        # Check if cue ball would hit any other ball (first collision only)
        if hit_ball_index is None:
            for i, other in enumerate(sim_balls):
                if i != cue_index and other.alive:
                    dx_ball = sim_cue.x - other.x
                    dy_ball = sim_cue.y - other.y
                    dist_ball = math.hypot(dx_ball, dy_ball)
                    if dist_ball < sim_cue.radius + other.radius + 2:
                        hit_ball_index = i
                        # Start tracking this object ball's trajectory
                        object_trajectories[i] = [(int(other.x), int(other.y))]
                        break
        
        # Update physics
        physics_step(sim_balls, dt)
        
        # Record cue ball position
        cue_trajectory.append((int(sim_cue.x), int(sim_cue.y)))
        
        # Record object ball positions after collision
        if hit_ball_index is not None:
            hit_ball = sim_balls[hit_ball_index]
            if hit_ball.alive:
                object_trajectories[hit_ball_index].append((int(hit_ball.x), int(hit_ball.y)))
        
        # Stop if cue ball is too slow or stopped
        speed = math.hypot(sim_cue.vx, sim_cue.vy)
        if speed < MIN_SPEED_THRESHOLD:
            break
    
    return cue_trajectory, hit_ball_index, object_trajectories


def main():
    pygame.init()
    pygame.display.set_caption("Computational Physics: Billiards & Momentum")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    # Setup: cue ball + 3 target balls
    ball_radius = 15  # Smaller balls
    balls = [
        Ball(
            x=WIDTH * 0.25,
            y=HEIGHT * 0.5,
            vx=0.0,
            vy=0.0,
            radius=ball_radius,
            mass=1.0,
            color=(250, 240, 240),
            is_cue=True,
        ),
        Ball(
            x=WIDTH * 0.55,
            y=HEIGHT * 0.45,
            vx=0.0,
            vy=0.0,
            radius=ball_radius,
            mass=1.0,
            color=(240, 200, 80),
        ),
        Ball(
            x=WIDTH * 0.55,
            y=HEIGHT * 0.55,
            vx=0.0,
            vy=0.0,
            radius=ball_radius,
            mass=1.0,
            color=(80, 160, 240),
        ),
        Ball(
            x=WIDTH * 0.7,
            y=HEIGHT * 0.5,
            vx=0.0,
            vy=0.0,
            radius=ball_radius,
            mass=1.0,
            color=(200, 100, 150),
        ),
    ]

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
                    # Auto-compute a decent shot (planner)
                    angle_deg, speed = find_shot_to_pot(balls)
                    if angle_deg is not None:
                        cue = balls[0]
                        theta = math.radians(angle_deg)
                        cue.vx = speed * math.cos(theta)
                        cue.vy = speed * math.sin(theta)
                        shot_message = f"Shot: angle={angle_deg}°, speed={speed:.0f}"
                        aiming = False
                    else:
                        shot_message = "No simple direct shot found"
                elif event.key == pygame.K_r:
                    # Simple reset: stop cue ball and re-enable aiming
                    cue = balls[0]
                    cue.vx = 0.0
                    cue.vy = 0.0
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
                # Left-click: shoot cue ball toward mouse with power based on distance
                cue = balls[0]
                if not cue.alive:
                    continue
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - cue.x
                dy = mouse_y - cue.y
                dist = math.hypot(dx, dy)
                if dist > 5.0:
                    dir_x = dx / dist
                    dir_y = dy / dist
                    # Use the adjustable shot power
                    cue.vx = dir_x * shot_power
                    cue.vy = dir_y * shot_power
                    aiming = False
                    shot_message = f"Manual shot: speed={shot_power:.0f}"

        # Update physics
        physics_step(balls, dt)

        # Compute totals for display
        Px, Py, KE = compute_totals(balls)

        # Draw
        draw_table(screen)
        for ball in balls:
            if ball.alive:
                ball.draw(screen)

        # Draw aiming arrow and trajectory preview from cue ball to mouse when cue is at rest
        cue = balls[0]
        if aiming and cue.alive:
            if abs(cue.vx) < 1e-2 and abs(cue.vy) < 1e-2:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                start = (int(cue.x), int(cue.y))
                
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


