import math
import constants as c


def resolve_ball_collisions(balls, restitution=None, iterations=3):
    """Resolve elastic ball-on-ball collisions for all alive pairs.

    Runs multiple passes so clustered balls settle without overlap.
    """
    if restitution is None:
        restitution = c.BALL_RESTITUTION

    for _ in range(iterations):
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                _resolve_pair(balls[i], balls[j], restitution)


def _resolve_pair(a, b, restitution):
    if not a.alive or not b.alive:
        return

    dx = b.x - a.x
    dy = b.y - a.y
    dist_sq = dx * dx + dy * dy
    min_dist = a.radius_px + b.radius_px

    if dist_sq >= min_dist * min_dist:
        return

    if dist_sq == 0:
        # Perfect overlap fallback: push apart along an arbitrary axis
        nx, ny = 1.0, 0.0
        dist = 0.0
    else:
        dist = math.sqrt(dist_sq)
        nx = dx / dist
        ny = dy / dist

    # Positional correction: split overlap by inverse mass ratio
    overlap = min_dist - dist
    total_mass = a.mass + b.mass
    a.x -= nx * overlap * (b.mass / total_mass)
    a.y -= ny * overlap * (b.mass / total_mass)
    b.x += nx * overlap * (a.mass / total_mass)
    b.y += ny * overlap * (a.mass / total_mass)

    # Relative velocity along collision normal
    dvx = b.vx - a.vx
    dvy = b.vy - a.vy
    vel_along_normal = dvx * nx + dvy * ny

    # Balls already separating — only fix overlap
    if vel_along_normal > 0:
        return

    # KEY EQUATION: impulse for 1D elastic collision along normal n
    # j = -(1 + e) * v_rel / (1/m_a + 1/m_b)
    j = -(1.0 + restitution) * vel_along_normal / (1.0 / a.mass + 1.0 / b.mass)

    a.vx -= (j / a.mass) * nx
    a.vy -= (j / a.mass) * ny
    b.vx += (j / b.mass) * nx
    b.vy += (j / b.mass) * ny
