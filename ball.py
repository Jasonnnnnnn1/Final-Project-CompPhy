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
        self.alive = True
        self.velocity = pygame.Vector2(0, 0)
        self.angular_velocity = 0.0

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
        return int(self.radius * c.PX_PER_M)

    @property
    def x(self):
        """Exposes physics position x in pixel coordinates for drawing and grid mapping."""
        return self.position.x * c.PX_PER_M

    @x.setter
    def x(self, px_val):
        self.position.x = px_val * c.M_PER_PX

    @property
    def y(self):
        """Exposes physics position y in pixel coordinates for drawing and grid mapping."""
        return self.position.y * c.PX_PER_M

    @y.setter
    def y(self, px_val):
        self.position.y = px_val * c.M_PER_PX

    @property
    def vx(self):
        return self.velocity.x    

    @vx.setter
    def vx(self, v):
        self.velocity.x = float(v)

    @property
    def vy(self):
        return self.velocity.y

    @vy.setter
    def vy(self, v):
        self.velocity.y = float(v)

    @property
    def speed(self):
        return self.velocity.length() # Utilizes Pygame's optimized vector length calculation

    @property
    def rolling_speed(self):
        return abs(self.angular_velocity) * self.radius        

    def is_sliding(self):
        return abs(self.speed - self.rolling_speed) > 0.05    

    def apply_force(self, force, direction: pygame.Vector2):
        force = max(c.MIN_FORCE, min(c.MAX_FORCE, force))
        impulse = force * c.CUE_CONTACT_TIME_S  

        if direction.length_squared() == 0:
            return
        unit_dir = direction.normalize()

        delta_v = impulse / self.mass              
        self.velocity += delta_v * unit_dir
        self.angular_velocity = 0.0

    def apply_sliding_friction(self, friction_coeff, dt):
        if self.speed < 0.001:                      
            self.velocity = pygame.Vector2(0, 0)
            self.angular_velocity = 0.0
            return

        # Calculate deceleration magnitude
        decel = friction_coeff * c.GRAVITY_MPS2
        velocity_loss = decel * dt
        if velocity_loss >= self.speed:
            # Move the ball by its remaining fractional distance before stopping
            # Average velocity over the short time fraction = speed / 2
            time_to_stop = self.speed / decel
            self.position += (self.velocity * 0.5) * time_to_stop
            self.velocity = pygame.Vector2(0, 0)
            self.angular_velocity = self.speed / self.radius # sets final expected spin
            return

        unit_vel = self.velocity.normalize()
        self.velocity -= decel * unit_vel * dt

        # Update spin spin_accel
        desired_spin = self.speed / self.radius
        spin_accel = (5.0 / 2.0) * decel / self.radius
        self.angular_velocity = min(self.angular_velocity + spin_accel * dt, desired_spin)

        self.position += self.velocity * dt            

    def apply_rolling_friction(self, friction_coeff, dt):
        # Stop the ball if speed less than 0.001
        if self.speed < 0.001:
            self.velocity = pygame.Vector2(0, 0)
            self.angular_velocity = 0.0
            return

        # Friction logic
        decel = friction_coeff * c.GRAVITY_MPS2   
        velocity_loss = decel * dt
        if velocity_loss >= self.speed:
            time_to_stop = self.speed / decel
            self.position += (self.velocity * 0.5) * time_to_stop
            self.velocity = pygame.Vector2(0, 0)
            self.angular_velocity = 0.0
            return  
        
        unit_vel = self.velocity.normalize()

        # Update the velocity components
        self.velocity -= decel * unit_vel * dt

        # Update the position using the new velocity
        self.position += self.velocity * dt

        if self.speed > 0:
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