import pygame
import constants as c

class Ball:
    def __init__(self, x_px, y_px, radius_m, mass, color, is_cue=False, is_black=False, image_path=None):
        # 1. Initialize the internal vector position FIRST (converts incoming pixels to meters)
        self.position = pygame.Vector2(x_px * c.M_PER_PX, y_px * c.M_PER_PX)
        
        # 2. Assign standard physics constants (all calculations run natively in meters)
        self.radius = radius_m            # Physics radius (meters)
        self.mass = mass
        self.color = color
        self.is_cue = is_cue
        self.is_black = is_black
        self.alive = True                 # Tracks if ball is still on table (not pocketed)
        self.velocity = pygame.Vector2(0, 0)   # Starts stationary
        self.angular_velocity = 0.0            # Rotational speed (rad/s), starts at rest

        # Image asset handling on the balls
        self.image = None
        if image_path:
            raw_image = pygame.image.load(image_path).convert_alpha()
            
            # Scale it perfectly to match the diameter (width and height = radius * 2)
            diameter = self.radius_px * 2
            self.image = pygame.transform.smoothscale(raw_image, (diameter, diameter))

    # --- SYNCHRONIZED PIXEL PROPERTIES ---
    @property
    def radius_px(self):
        """Dynamic converter mapping radius meters to current runtime screen scale pixels."""
        # EQUATIONS: pixels = meters * (pixels / meter)
        return int(self.radius * c.PX_PER_M)

    @property
    def x(self):
        """Exposes physics position x in pixel coordinates for drawing and grid mapping."""
        # EQUATIONS: x_px = x_m * (pixels / meter)
        return self.position.x * c.PX_PER_M

    @x.setter
    def x(self, px_val):
        # EQUATIONS: x_m = x_px * (meters / pixel)
        self.position.x = px_val * c.M_PER_PX

    @property
    def y(self):
        """Exposes physics position y in pixel coordinates for drawing and grid mapping."""
        # EQUATIONS: y_px = y_m * (pixels / meter)
        return self.position.y * c.PX_PER_M

    @y.setter
    def y(self, px_val):
        # EQUATIONS: y_m = y_px * (meters / pixel)
        self.position.y = px_val * c.M_PER_PX

    @property
    def vx(self):
        return self.velocity.x    

    @vx.setter
    def vx(self, v):
        self.velocity.x = float(v)   # Force float to keep vector math consistent

    @property
    def vy(self):
        return self.velocity.y

    @vy.setter
    def vy(self, v):
        self.velocity.y = float(v)   # Force float to keep vector math consistent

    @property
    def speed(self):
        # EQUATIONS: speed = sqrt(vx^2 + vy^2)
        return self.velocity.length() # Magnitude of velocity

    @property
    def rolling_speed(self):
        # EQUATIONS: v_rolling = omega * r (linear speed at contact point from pure rolling)
        return abs(self.angular_velocity) * self.radius        

    def is_sliding(self):
        # Ball is sliding when its translational speed and rolling speed don't match
        # EQUATIONS: sliding if |v - omega*r| > threshold
        return abs(self.speed - self.rolling_speed) > 0.05    

    def apply_force(self, force, direction: pygame.Vector2):
        # Clamp force within allowed min/max before applying
        force = max(c.MIN_FORCE, min(c.MAX_FORCE, force))
        # EQUATIONS: impulse = force * delta_t
        impulse = force * c.CUE_CONTACT_TIME_S  

        # Can't apply force with no direction
        if direction.length_squared() == 0:
            return
        unit_dir = direction.normalize()   # Strip magnitude, keep only direction

        # EQUATIONS: delta_v = impulse / mass  (impulse-momentum theorem: J = m * delta_v)
        delta_v = impulse / self.mass              
        self.velocity += delta_v * unit_dir
        self.angular_velocity = 0.0   # Reset spin — cue hit is assumed to be center-ball

    def apply_sliding_friction(self, friction_coeff, dt):
        # First check if speed is super slow, if it is just get rid of all velocities
        if self.speed < 0.001:                      
            self.velocity = pygame.Vector2(0, 0)
            self.angular_velocity = 0.0
            return

        # EQUATIONS: a = f * g 
        decel = friction_coeff * c.GRAVITY_MPS2
        # EQUATIONS: a = dv / dt
        velocity_loss = decel * dt
        # If the change in velocity is bigger than the current speed of the ball:
        if velocity_loss >= self.speed:
            # Move the ball by its remaining fractional distance before stopping
            # Average velocity over the short time fraction = speed / 2
            # EQUATIONS: dt = dv / a
            time_to_stop = self.speed / decel
            # EQUATIONS: distance = v * t
            self.position += (self.velocity * 0.5) * time_to_stop
            # Get rid of the ball's velocity fully
            self.velocity = pygame.Vector2(0, 0)
            # sets final expected spin
            self.angular_velocity = self.speed / self.radius 
            return

        # normalized velocity = uv
        unit_vel = self.velocity.normalize()
        
        # EQUATIONS: v_new = v - a * uv * dt  (decelerate along current direction of motion)
        self.velocity -= decel * unit_vel * dt

        # Update spin spin_accel
        # EQUATIONS: alpha = (5/2) * a / r  (rolling contact point angular acceleration)
        desired_spin = self.speed / self.radius
        spin_accel = (5.0 / 2.0) * decel / self.radius
        # Spin builds up but never exceeds the pure-rolling value
        self.angular_velocity = min(self.angular_velocity + spin_accel * dt, desired_spin)

        # EQUATIONS: x_new = x + v * dt  (Euler integration step)
        self.position += self.velocity * dt            

    def apply_rolling_friction(self, friction_coeff, dt):
        # Stop the ball if speed less than 0.001
        if self.speed < 0.001:
            self.velocity = pygame.Vector2(0, 0)
            self.angular_velocity = 0.0
            return

        # Friction logic
        # EQUATIONS: a = mu * g
        decel = friction_coeff * c.GRAVITY_MPS2   
        # EQUATIONS: delta_v = a * dt
        velocity_loss = decel * dt
        if velocity_loss >= self.speed:
            # EQUATIONS: dt = v / a  (time remaining until full stop)
            time_to_stop = self.speed / decel
            # EQUATIONS: distance = (v / 2) * t  (average velocity to final stop)
            self.position += (self.velocity * 0.5) * time_to_stop
            self.velocity = pygame.Vector2(0, 0)
            self.angular_velocity = 0.0   # Pure rolling fully stopped, spin is zero
            return  
        
        unit_vel = self.velocity.normalize()   # Direction of motion only

        # Update the velocity components
        # EQUATIONS: v_new = v - a * uv * dt
        self.velocity -= decel * unit_vel * dt

        # Update the position using the new velocity (Semi-implicit Euler!)
        # EQUATIONS: x_new = x + v * dt  
        self.position += self.velocity * dt

        if self.speed > 0:
            # EQUATIONS: omega = v / r  (pure rolling constraint: contact point has zero slip)
            self.angular_velocity = self.speed / self.radius

    def update(self, dt):
        if not self.alive:
            return
        if self.is_sliding():
            self.apply_sliding_friction(c.SLIDING_FRICTION, dt)
        else:
            self.apply_rolling_friction(c.ROLLING_FRICTION, dt)

    def draw(self, surface):
        if not self.alive:
            return
        if self.image:
            # Snap image center directly to the converted pixel coordinates
            rect = self.image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.image, rect.topleft)
        else:
            # Clean fallback: uses our dynamic pixel property conversion getters
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius_px)