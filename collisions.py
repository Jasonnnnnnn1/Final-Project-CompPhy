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

    # First, we use the Pythagorean theorem to check the distance between the two balls.
    # If the distance is smaller than the sum of their radii, it means they are touching and a collision has happened!
    dx = b.x - a.x
    dy = b.y - a.y
    # EQUATIONS: distance^2 = dx^2 + dy^2 (Pythagorean Theorem)
    dist_sq = dx * dx + dy * dy
    # EQUATIONS: minimum_distance = R_a + R_b (Collision Threshold)
    min_dist = a.radius_px + b.radius_px

    if dist_sq >= min_dist * min_dist:
        return

    if dist_sq == 0:
        # Perfect overlap fallback: push apart along an arbitrary axis
        nx, ny = 1.0, 0.0
        dist = 0.0
    else:
        dist = math.sqrt(dist_sq)
        # We calculate the 'Normal Vector', which is an invisible line connecting the centers of the two balls.
        # Physics dictates that the momentum will be transferred exactly along this line.
        # EQUATIONS: Normal Vector N(nx, ny) = (dx/dist, dy/dist)
        nx = dx / dist
        ny = dy / dist

    # If the balls overlap slightly due to discrete frame-rates, we gently 
    # push them apart based on their masses so they don't get permanently stuck inside each other.
    # Positional correction: split overlap by inverse mass ratio
    # EQUATIONS: Overlap depth = sum_radii - actual_distance
    overlap = min_dist - dist
    total_mass = a.mass + b.mass
    a.x -= nx * overlap * (b.mass / total_mass)
    a.y -= ny * overlap * (b.mass / total_mass)
    b.x += nx * overlap * (a.mass / total_mass)
    b.y += ny * overlap * (a.mass / total_mass)

    # Next, we use a Dot Product to isolate exactly how fast the balls 
    # are moving directly towards each other along that Normal Vector line.
    # Relative velocity along collision normal
    # EQUATIONS: v_rel = (V_b - V_a)
    dvx = b.vx - a.vx
    dvy = b.vy - a.vy
    # EQUATIONS: v_normal = v_rel DOT N (Projecting velocity onto the normal line)
    vel_along_normal = dvx * nx + dvy * ny

    # Balls already separating — only fix overlap
    if vel_along_normal > 0:
        return

    # Here we calculate the physical Impulse (force over time) of the collision.
    # We use a Coefficient of Restitution to simulate the tiny bit of energy lost to heat and the 'clack' sound!
    # KEY EQUATION: impulse for 1D elastic collision along normal n
    # EQUATIONS: j = -(1 + e) * v_normal / (1/m_a + 1/m_b)
    # ('e' is the Coefficient of Restitution representing inelastic energy loss)
    j = -(1.0 + restitution) * vel_along_normal / (1.0 / a.mass + 1.0 / b.mass)

    # Finally, we apply that Impulse to change the velocities of both balls, sending them bouncing apart.
    # EQUATIONS: V_final = V_initial +/- (Impulse / Mass) * Normal_Vector
    a.vx -= (j / a.mass) * nx
    a.vy -= (j / a.mass) * ny
    b.vx += (j / b.mass) * nx
    b.vy += (j / b.mass) * ny
