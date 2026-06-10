import math
import pygame
import constants as c

LINE_COLOR = (255, 255, 255)
LINE_WIDTH = 2
GHOST_RING_WIDTH = 2

def calculate_kinematics(v0):
    """Calculate exact stopping distance taking into account sliding and rolling friction phases."""
    if v0 <= 0.001:
        return 0.0, 0.0, 0.0
        
    a_slide = c.SLIDING_FRICTION * c.GRAVITY_MPS2
    a_roll = c.ROLLING_FRICTION * c.GRAVITY_MPS2
    
    # To calculate the stopping distance, we run the initial velocity through two friction states.
    # First, the Sliding Phase decelerates the ball quickly because it's skidding across the felt.
    # Distance traveled during the sliding phase
    # EQUATIONS: d_slide = (12 * v0^2) / (49 * u_slide * g)
    d_slide = (12.0 * v0**2) / (49.0 * a_slide)
    
    # Velocity at the moment the ball begins pure rolling
    # EQUATIONS: v_roll = (5/7) * v0
    v_roll = (5.0 / 7.0) * v0
    
    # Once the ball stops skidding, it enters the Pure Rolling phase, where friction is much lower, letting it glide!
    # Distance traveled during the pure rolling phase
    # EQUATIONS: d_roll = (v_roll^2) / (2 * u_roll * g)
    d_roll = (v_roll**2) / (2.0 * a_roll)
    
    # Total stopping distance
    d_stop = d_slide + d_roll
    return d_stop, d_slide, v_roll

def get_velocity_at_distance(v0, d, d_slide, v_roll):
    """Calculate the remaining velocity of a ball after it has traveled distance d (in meters)."""
    if d <= 0:
        return v0
        
    a_slide = c.SLIDING_FRICTION * c.GRAVITY_MPS2
    a_roll = c.ROLLING_FRICTION * c.GRAVITY_MPS2
    
    if d <= d_slide:
        # EQUATIONS: V_final^2 = V_initial^2 - 2 * a * d
        v_sq = v0**2 - 2 * a_slide * d
        return math.sqrt(max(0, v_sq))
    else:
        d_in_roll = d - d_slide
        # EQUATIONS: V_final^2 = V_initial^2 - 2 * a * d
        v_sq = v_roll**2 - 2 * a_roll * d_in_roll
        return math.sqrt(max(0, v_sq))

def get_ghost_aim(cue_ball, balls, aim_dir, force):
    if aim_dir.length_squared() < 1e-6:
        return None

    aim_dir = aim_dir.normalize()
    cue_pos = pygame.Vector2(cue_ball.x, cue_ball.y)
    
    # Calculate cue ball initial kinematics
    v0_m = (force * c.CUE_CONTACT_TIME_S) / c.BALL_MASS
    d_stop_m, d_slide_m, v_roll_m = calculate_kinematics(v0_m)
    d_stop_px = d_stop_m * c.PX_PER_M
    
    best_t = float('inf')
    best_ball = None

    # Find the first ball we hit
    for ball in balls:
        if not ball.alive or ball.is_cue:
            continue
            
        obj_pos = pygame.Vector2(ball.x, ball.y)
        d_vec = cue_pos - obj_pos
        
        # Here is our Continuous Collision Detection. We cast a Ray and use the 
        # Quadratic Formula to find the exact pixel where it intersects a boundary circle drawn around the target ball!
        # Ray-circle intersection quadratic formula (at^2 + bt + c = 0)
        # EQUATIONS: a = (V dot V) = 1 (since aim_dir is normalized)
        # EQUATIONS: b = 2 * (D dot V)
        b = 2.0 * d_vec.dot(aim_dir)
        # EQUATIONS: c = (D dot D) - (2R)^2
        c_val = d_vec.length_squared() - (2.0 * cue_ball.radius_px) ** 2
        
        # EQUATIONS: Discriminant = b^2 - 4ac
        disc = b * b - 4.0 * c_val
        
        if disc >= 0:
            # EQUATIONS: t = (-b +/- sqrt(disc)) / 2a
            sqrt_disc = math.sqrt(disc)
            t1 = (-b - sqrt_disc) * 0.5
            t2 = (-b + sqrt_disc) * 0.5
            
            # Find smallest positive t
            hit_t = None
            if t1 > 1e-4:
                hit_t = t1
            elif t2 > 1e-4:
                hit_t = t2
                
            if hit_t is not None and hit_t < best_t:
                best_t = hit_t
                best_ball = ball

    # If no ball is hit, or the ball stops before hitting the target
    if best_ball is None or best_t > d_stop_px:
        # Provide a straight line to the stopping point
        end_pos = cue_pos + aim_dir * d_stop_px
        return {
            "cue_pos": cue_pos,
            "ghost_pos": None, # Indicates cue stops before hit
            "cue_stop_pos": end_pos
        }

    ghost_pos = cue_pos + aim_dir * best_t
    obj_pos = pygame.Vector2(best_ball.x, best_ball.y)
    
    # Calculate collision physics!
    dist_to_ghost_m = best_t * c.M_PER_PX
    v_impact_m = get_velocity_at_distance(v0_m, dist_to_ghost_m, d_slide_m, v_roll_m)
    
    # Normal vector from ghost ball to object ball
    n = (obj_pos - ghost_pos)
    if n.length_squared() < 1e-6:
        n = aim_dir
    else:
        n = n.normalize()

    cos_theta = aim_dir.dot(n)
    
    # We calculate a 1D elastic collision along the Normal Vector to find how much energy is transferred to the object ball.
    # 1D Elastic Collision along the normal axis
    # Equal mass, so dv = (1+e)*v_rel / 2
    # Object ball is at rest, so v_rel = v_impact * cos_theta
    # EQUATIONS: dV = ((1 + e) / 2) * (V_impact * cos_theta)
    dv = ((1.0 + c.BALL_RESTITUTION) / 2.0) * (v_impact_m * cos_theta)
    
    v_out_obj_m = dv
    v_out_cue_n_m = (v_impact_m * cos_theta) - dv
    
    # Because elastic collisions always separate at 90 degrees, we find the Tangent Vector
    # by subtracting the Normal vector from the original aim direction. The cue ball deflects exactly down this tangent line!
    # Calculate Tangent Deflection
    # EQUATIONS: Tangent_Vector = Aim_Dir - (Normal * cos_theta)
    tangent_vec = aim_dir - n * cos_theta
    if tangent_vec.length_squared() < 1e-6:
        v_out_cue_t_m = 0
        deflect_dir = None
    else:
        deflect_dir = tangent_vec.normalize()
        v_out_cue_t_m = v_impact_m * tangent_vec.length()

    v_out_cue_m = math.sqrt(v_out_cue_n_m**2 + v_out_cue_t_m**2)
    
    # Calculate stopping distances for both balls post-collision
    obj_d_stop_m, _, _ = calculate_kinematics(v_out_obj_m)
    cue_d_stop_m, _, _ = calculate_kinematics(v_out_cue_m)
    
    obj_path_len_px = obj_d_stop_m * c.PX_PER_M
    cue_path_len_px = cue_d_stop_m * c.PX_PER_M

    return {
        "cue_pos": cue_pos,
        "ghost_pos": ghost_pos,
        "object_ball": best_ball,
        "object_dir": n,
        "cue_deflect_dir": deflect_dir,
        "obj_path_len_px": obj_path_len_px,
        "cue_path_len_px": cue_path_len_px
    }

def draw_ghost_indicator(surface, cue_ball, balls, aim_dir, force):
    """8 Ball Pool style: white ring ghost + exactly scaled guide lines."""
    shot = get_ghost_aim(cue_ball, balls, aim_dir, force)
    if shot is None:
        return

    cue_pos = shot["cue_pos"]
    
    # If the cue ball stops before hitting anything
    if shot["ghost_pos"] is None:
        stop_pos = shot["cue_stop_pos"]
        cx, cy = int(cue_pos.x), int(cue_pos.y)
        sx, sy = int(stop_pos.x), int(stop_pos.y)
        pygame.draw.line(surface, LINE_COLOR, (cx, cy), (sx, sy), LINE_WIDTH)
        return

    r = int(cue_ball.radius_px)
    ghost_pos = shot["ghost_pos"]
    obj_dir = shot["object_dir"]
    deflect_dir = shot["cue_deflect_dir"]
    
    obj_len = shot["obj_path_len_px"]
    cue_len = shot["cue_path_len_px"]

    cx, cy = int(cue_pos.x), int(cue_pos.y)
    gx, gy = int(ghost_pos.x), int(ghost_pos.y)

    obj_end = ghost_pos + obj_dir * (obj_len + 2.0 * r)
    
    # 1) Cue ball → ghost ball
    pygame.draw.line(surface, LINE_COLOR, (cx, cy), (gx, gy), LINE_WIDTH)

    # 2) Ghost → through object ball
    if obj_len > 0:
        pygame.draw.line(
            surface, LINE_COLOR,
            (gx, gy), (int(obj_end.x), int(obj_end.y)), LINE_WIDTH
        )

    # 3) Cue deflection
    if deflect_dir is not None and cue_len > 0:
        deflect_end = ghost_pos + deflect_dir * cue_len
        pygame.draw.line(
            surface, LINE_COLOR,
            (gx, gy), (int(deflect_end.x), int(deflect_end.y)), LINE_WIDTH
        )

    # Ghost ball ring (outline only)
    pygame.draw.circle(surface, LINE_COLOR, (gx, gy), r, GHOST_RING_WIDTH)
