import math
import sys
import pygame

WIDTH, HEIGHT = 900, 500
TABLE_MARGIN = 50
FPS = 60

BG_COLOR = (20, 120, 40)
RAIL_COLOR = (10, 60, 20)
TEXT_COLOR = (240, 240, 240)

BALL_ELASTICITY = 0.92
SPACE_DAMPING = 0.45
MIN_SPEED = 15.0
SHOT_CONTACT_TIME = 0.05
IMPACT_CONTACT_TIME = 0.012

POCKET_RADIUS = 26
POCKET_POSITIONS = [
    (TABLE_MARGIN + 5, TABLE_MARGIN + 5),
    (WIDTH - TABLE_MARGIN - 5, TABLE_MARGIN + 5),
    (TABLE_MARGIN + 5, HEIGHT - TABLE_MARGIN - 5),
    (WIDTH - TABLE_MARGIN - 5, HEIGHT - TABLE_MARGIN - 5),
    (WIDTH // 2, TABLE_MARGIN + 5),
    (WIDTH // 2, HEIGHT - TABLE_MARGIN - 5),
]


class Ball:
    def __init__(self, x, y, radius, mass, color, is_cue=False):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0.0, 0.0)
        self.radius = radius
        self.mass = mass
        self.color = color
        self.is_cue = bool(is_cue)
        self.alive = True

    @property
    def x(self):
        return self.pos.x

    @property
    def y(self):
        return self.pos.y

    @property
    def vx(self):
        return self.vel.x

    @property
    def vy(self):
        return self.vel.y

    def draw(self, surface):
        if self.alive:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def clone(self):
        b = Ball(self.x, self.y, self.radius, self.mass, self.color, self.is_cue)
        b.vel = pygame.Vector2(self.vel.x, self.vel.y)
        b.alive = self.alive
        return b


def build_balls(ball_specs):
    return [Ball(x, y, radius, mass, color, is_cue) for (x, y, radius, mass, color, is_cue) in ball_specs]


def compute_totals(balls):
    px = py = ke = 0.0
    for b in balls:
        if not b.alive:
            continue
        px += b.mass * b.vx
        py += b.mass * b.vy
        ke += 0.5 * b.mass * (b.vx * b.vx + b.vy * b.vy)
    return px, py, ke


def draw_table(surface):
    surface.fill(RAIL_COLOR)
    pygame.draw.rect(
        surface,
        BG_COLOR,
        pygame.Rect(TABLE_MARGIN, TABLE_MARGIN, WIDTH - 2 * TABLE_MARGIN, HEIGHT - 2 * TABLE_MARGIN),
        border_radius=20,
    )
    for (px, py) in POCKET_POSITIONS:
        pygame.draw.circle(surface, (0, 0, 0), (int(px), int(py)), POCKET_RADIUS)


def handle_pocketing(balls):
    for b in balls:
        if not b.alive or b.is_cue:
            continue
        for (px, py) in POCKET_POSITIONS:
            if (b.x - px) ** 2 + (b.y - py) ** 2 <= POCKET_RADIUS ** 2:
                b.alive = False
                b.vel.update(0.0, 0.0)
                break


def resolve_wall_collision(ball):
    if not ball.alive:
        return
    left = TABLE_MARGIN + ball.radius
    right = WIDTH - TABLE_MARGIN - ball.radius
    top = TABLE_MARGIN + ball.radius
    bottom = HEIGHT - TABLE_MARGIN - ball.radius

    if ball.x < left:
        ball.pos.x = left
        ball.vel.x *= -BALL_ELASTICITY
    elif ball.x > right:
        ball.pos.x = right
        ball.vel.x *= -BALL_ELASTICITY

    if ball.y < top:
        ball.pos.y = top
        ball.vel.y *= -BALL_ELASTICITY
    elif ball.y > bottom:
        ball.pos.y = bottom
        ball.vel.y *= -BALL_ELASTICITY


def resolve_ball_collision(a, b):
    if not a.alive or not b.alive:
        return False, 0.0

    delta = b.pos - a.pos
    dist = delta.length()
    min_dist = a.radius + b.radius
    if dist <= 0.0 or dist >= min_dist:
        return False, 0.0

    normal = delta / dist
    overlap = min_dist - dist
    total_mass = a.mass + b.mass

    a.pos -= normal * (overlap * (b.mass / total_mass))
    b.pos += normal * (overlap * (a.mass / total_mass))

    rel_vel = b.vel - a.vel
    vel_normal = rel_vel.dot(normal)
    if vel_normal > 0:
        return False, 0.0

    e = BALL_ELASTICITY
    j = -(1 + e) * vel_normal
    j /= (1 / a.mass + 1 / b.mass)
    impulse = normal * j

    a.vel -= impulse / a.mass
    b.vel += impulse / b.mass
    return True, j


def physics_step(balls, dt):
    collisions = []
    damping_scale = max(0.0, 1.0 - SPACE_DAMPING * dt)

    for b in balls:
        if not b.alive:
            continue
        b.pos += b.vel * dt
        b.vel *= damping_scale
        if b.vel.length() < MIN_SPEED:
            b.vel.update(0.0, 0.0)
        resolve_wall_collision(b)

    for i in range(len(balls)):
        if not balls[i].alive:
            continue
        for j in range(i + 1, len(balls)):
            did_collide, impulse_mag = resolve_ball_collision(balls[i], balls[j])
            if did_collide:
                collisions.append((i, j, impulse_mag))

    handle_pocketing(balls)
    return collisions


def clone_balls(balls):
    return [b.clone() for b in balls]


def simulate_shot(balls, target_index, angle_deg, speed, seconds=6.0, dt=1 / 180):
    sim = clone_balls(balls)
    cue = sim[0]
    theta = math.radians(angle_deg)
    cue.vel = pygame.Vector2(speed * math.cos(theta), speed * math.sin(theta))

    steps = int(seconds / dt)
    for _ in range(steps):
        physics_step(sim, dt)
        if target_index < len(sim) and not sim[target_index].alive:
            return True
    return False


def find_shot_to_pot(balls, target_index=1):
    speed = 500.0
    for angle_deg in range(0, 360, 3):
        if simulate_shot(balls, target_index, angle_deg, speed):
            return angle_deg, speed
    return None, None


def predict_trajectory(balls, target_pos, shot_speed=400.0, max_steps=180):
    if not balls[0].alive:
        return [], None, {}

    cue = balls[0]
    aim = pygame.Vector2(target_pos[0] - cue.x, target_pos[1] - cue.y)
    if aim.length() < 5.0:
        return [], None, {}
    aim = aim.normalize()

    sim = clone_balls(balls)
    sim[0].vel = aim * shot_speed

    cue_trajectory = []
    hit_ball_index = None
    object_trajectories = {}
    dt = 1 / 90

    for _ in range(max_steps):
        if sim[0].alive:
            cue_trajectory.append((int(sim[0].x), int(sim[0].y)))
        collisions = physics_step(sim, dt)

        if hit_ball_index is None:
            for i, j, _ in collisions:
                if i == 0:
                    hit_ball_index = j
                    object_trajectories[j] = [(int(sim[j].x), int(sim[j].y))]
                    break
                if j == 0:
                    hit_ball_index = i
                    object_trajectories[i] = [(int(sim[i].x), int(sim[i].y))]
                    break
        elif hit_ball_index < len(sim) and sim[hit_ball_index].alive:
            object_trajectories[hit_ball_index].append((int(sim[hit_ball_index].x), int(sim[hit_ball_index].y)))

        if sim[0].vel.length() < MIN_SPEED:
            break

    return cue_trajectory, hit_ball_index, object_trajectories


def format_first_hit(idx):
    if idx is None:
        return "None"
    return f"Ball {idx}"


def set_power_from_bar(mouse_y, bar_top, bar_height, min_power, max_power):
    clamped_y = max(bar_top, min(mouse_y, bar_top + bar_height))
    ratio = 1.0 - ((clamped_y - bar_top) / bar_height)
    return min_power + ratio * (max_power - min_power)


def main():
    pygame.init()
    pygame.display.set_caption("Computational Physics: Billiards (Custom Physics)")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 18)

    ball_radius = 15
    ball_specs = [
        (WIDTH * 0.25, HEIGHT * 0.5, ball_radius, 1.0, (250, 240, 240), True),
        (WIDTH * 0.55, HEIGHT * 0.45, ball_radius, 1.0, (240, 200, 80), False),
        (WIDTH * 0.55, HEIGHT * 0.55, ball_radius, 1.0, (80, 160, 240), False),
        (WIDTH * 0.7, HEIGHT * 0.5, ball_radius, 1.0, (200, 100, 150), False),
    ]
    balls = build_balls(ball_specs)

    shot_message = "Move mouse to aim, click to shoot, SPACE for auto-shot"
    shot_power = 400.0
    min_shot_power = 200.0
    max_shot_power = 800.0

    shot_angle_deg = 0.0
    first_hit_ball = None
    applied_force = 0.0
    first_hit_force = 0.0
    metric_momentum_change = 0.0
    pre_shot_momentum = pygame.Vector2(0.0, 0.0)
    cue_trail = []

    bar_width = 24
    bar_height = 260
    bar_x = WIDTH - 34
    bar_y = (HEIGHT - bar_height) // 2
    dragging_power_bar = False

    running = True
    aiming = True

    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    angle_deg, speed = find_shot_to_pot(balls)
                    if angle_deg is not None and balls[0].alive:
                        theta = math.radians(angle_deg)
                        pre_shot_momentum = pygame.Vector2(*compute_totals(balls)[:2])
                        balls[0].vel = pygame.Vector2(speed * math.cos(theta), speed * math.sin(theta))
                        shot_angle_deg = angle_deg
                        applied_force = balls[0].mass * speed / SHOT_CONTACT_TIME
                        first_hit_ball = None
                        first_hit_force = 0.0
                        cue_trail = [(int(balls[0].x), int(balls[0].y))]
                        shot_message = f"Auto shot: angle={angle_deg} deg, speed={speed:.0f}"
                        aiming = False
                    else:
                        shot_message = "No direct pot shot found"
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    shot_power = min(shot_power + 50.0, max_shot_power)
                    shot_message = f"Shot power: {shot_power:.0f}"
                elif event.key == pygame.K_MINUS:
                    shot_power = max(shot_power - 50.0, min_shot_power)
                    shot_message = f"Shot power: {shot_power:.0f}"
                elif event.key == pygame.K_r:
                    balls = build_balls(ball_specs)
                    aiming = True
                    first_hit_ball = None
                    applied_force = 0.0
                    first_hit_force = 0.0
                    metric_momentum_change = 0.0
                    cue_trail = []
                    shot_message = "Reset table"
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    shot_power = min(shot_power + 30.0, max_shot_power)
                else:
                    shot_power = max(shot_power - 30.0, min_shot_power)
                shot_message = f"Shot power: {shot_power:.0f}"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_x, mouse_y = event.pos
                bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
                if bar_rect.collidepoint(mouse_x, mouse_y):
                    dragging_power_bar = True
                    shot_power = set_power_from_bar(mouse_y, bar_y, bar_height, min_shot_power, max_shot_power)
                    shot_message = f"Shot power: {shot_power:.0f}"
                elif balls[0].alive:
                    aim = pygame.Vector2(mouse_x - balls[0].x, mouse_y - balls[0].y)
                    if aim.length() > 5.0:
                        direction = aim.normalize()
                        speed = shot_power
                        pre_shot_momentum = pygame.Vector2(*compute_totals(balls)[:2])
                        balls[0].vel = direction * speed
                        shot_angle_deg = math.degrees(math.atan2(direction.y, direction.x))
                        applied_force = balls[0].mass * speed / SHOT_CONTACT_TIME
                        first_hit_ball = None
                        first_hit_force = 0.0
                        cue_trail = [(int(balls[0].x), int(balls[0].y))]
                        shot_message = f"Manual shot: angle={shot_angle_deg:.1f} deg, speed={speed:.0f}"
                        aiming = False
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_power_bar = False
            elif event.type == pygame.MOUSEMOTION and dragging_power_bar:
                shot_power = set_power_from_bar(event.pos[1], bar_y, bar_height, min_shot_power, max_shot_power)
                shot_message = f"Shot power: {shot_power:.0f}"

        collisions = physics_step(balls, dt)
        for i, j, impulse_mag in collisions:
            if first_hit_ball is None and (i == 0 or j == 0):
                first_hit_ball = j if i == 0 else i
                first_hit_force = impulse_mag / IMPACT_CONTACT_TIME

        px, py, ke = compute_totals(balls)
        current_momentum = pygame.Vector2(px, py)
        metric_momentum_change = (current_momentum - pre_shot_momentum).length()

        if balls[0].alive and balls[0].vel.length() >= MIN_SPEED:
            cue_trail.append((int(balls[0].x), int(balls[0].y)))
            if len(cue_trail) > 220:
                cue_trail.pop(0)
        elif balls[0].vel.length() < MIN_SPEED and not aiming:
            aiming = True

        draw_table(screen)
        for b in balls:
            b.draw(screen)

        if len(cue_trail) > 1:
            for i in range(len(cue_trail) - 1):
                pygame.draw.line(screen, (255, 245, 160), cue_trail[i], cue_trail[i + 1], 2)

        cue = balls[0]
        if aiming and cue.alive and cue.vel.length() < MIN_SPEED:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            start = (int(cue.x), int(cue.y))

            cue_trajectory, _, object_trajectories = predict_trajectory(balls, (mouse_x, mouse_y), shot_power)
            if len(cue_trajectory) > 1:
                for i in range(len(cue_trajectory) - 1):
                    pygame.draw.line(screen, (255, 255, 200), cue_trajectory[i], cue_trajectory[i + 1], 2)
                for i in range(0, len(cue_trajectory), 10):
                    pygame.draw.circle(screen, (255, 255, 200), cue_trajectory[i], 3)

            for obj_traj in object_trajectories.values():
                if len(obj_traj) > 1:
                    for i in range(len(obj_traj) - 1):
                        pygame.draw.line(screen, (100, 200, 255), obj_traj[i], obj_traj[i + 1], 2)

            end_vec = pygame.Vector2(mouse_x - cue.x, mouse_y - cue.y)
            if end_vec.length() > 0:
                if end_vec.length() > 160:
                    end_vec.scale_to_length(160)
                end = (int(cue.x + end_vec.x), int(cue.y + end_vec.y))
                pygame.draw.line(screen, (255, 255, 255), start, end, 3)
                head_size = 10
                angle = math.atan2(end_vec.y, end_vec.x)
                left = (int(end[0] - head_size * math.cos(angle - math.pi / 6)), int(end[1] - head_size * math.sin(angle - math.pi / 6)))
                right = (int(end[0] - head_size * math.cos(angle + math.pi / 6)), int(end[1] - head_size * math.sin(angle + math.pi / 6)))
                pygame.draw.polygon(screen, (255, 255, 255), [end, left, right])

        # Side power bar (drag/click to set shot strength)
        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (35, 35, 35), bar_rect, border_radius=6)
        power_ratio = (shot_power - min_shot_power) / (max_shot_power - min_shot_power)
        fill_h = int(bar_height * power_ratio)
        fill_rect = pygame.Rect(bar_x, bar_y + (bar_height - fill_h), bar_width, fill_h)
        pygame.draw.rect(screen, (255, 120, 90), fill_rect, border_radius=6)
        pygame.draw.rect(screen, (230, 230, 230), bar_rect, width=2, border_radius=6)

        any_ball_moving = any(b.alive and b.vel.length() >= MIN_SPEED for b in balls)
        if not any_ball_moving:
            text_lines = [
                f"Total Px: {px:7.2f}",
                f"Total Py: {py:7.2f}",
                f"Total KE: {ke:7.2f}",
                f"Angle (deg): {shot_angle_deg:7.2f}",
                f"First hit: {format_first_hit(first_hit_ball)}",
                f"Force estimate (N): {applied_force:7.2f}",
                f"First-hit force (N): {first_hit_force:7.2f}",
                f"Metric |delta p|: {metric_momentum_change:7.2f}",
                f"Shot Power: {shot_power:.0f} (+/-, wheel, or side bar)",
                "ESC quit, R reset",
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


