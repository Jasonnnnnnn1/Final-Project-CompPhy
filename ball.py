import pygame
import math

MIN_FORCE = 1
MAX_FORCE = 3000

class Ball:
    def __init__(self, body, shape, radius, mass, color, is_cue=False):
        self.body = body
        self.shape = shape
        self.radius = radius
        self.mass = mass
        self.color = color
        self.is_cue = is_cue
        self.alive = True # Ball is not pocketed

    # Position components
    @property
    def x(self):
        return self.body.position.x if self.body else 0.0
    @property
    def y(self):
        return self.body.position.y if self.body else 0.0
    
    # Velocity components
    @property
    def vx(self):
        return self.body.velocity.x if self.body else 0.0
    @property
    def vy(self):
        return self.body.velocity.y if self.body else 0.0

    # Get position method
    @property
    def position(self):
        return pygame.Vector2(self.x, self.y)

    # Get velocity method
    @property
    def velocity(self):
        return pygame.Vector2(self.vx, self.vy)
    
    # Get the speed of the ball (hypotenuse of both velocity components)
    @property
    def speed(self):
        return math.hypot(self.vx, self.vy)

    # Applying the force to the ball object
    def apply_force(self, force, direction: pygame.Vector2, dt=1/60.0):
        if not self.body:
            return
        
        # Set the force to the very max or the very min even if the user keeps on adding on it (surpassing the bar)
        force = max(MIN_FORCE, min(MIN_FORCE, force))

        impulse = force * dt

        # Normalizing the direction to get the unit vectors
        length = math.hypot(direction.x, direction.y)
        if length == 0:
            return
        # UNIT components
        ux = direction.x / length
        uy = direction.y / length

        # Calculate the new velocity components from the impulse
        new_vx = self.vx + (impulse * ux) / self.mass
        new_vy = self.vy + (impulse * uy) / self.mass
        self.body.velocity = new_vx, new_vy

    # Apply friction to the ball for every frame
    def apply_friction(self, friction_coeff, dt=1/60.0):
        if not self.body or not self.alive:
            return
        
        # Stop the ball if the speed is already very very very low
        if self.speed < 0.5:
            self.body.velocity = (0, 0)
            return
        
        # Frictional force acting on the ball = μ * m * g
        friction_force = friction_coeff * self.mass * 9.81

        # Direction opposing motion
        ux = -self.vx / self.speed
        uy = -self.vy / self.speed

        ax = (friction_force * ux) / self.mass
        ay = (friction_force * uy) / self.mass

        # Semi-implicit: velocity first
        new_vx = self.vx + ax * dt
        new_vy = self.vy + ay * dt

        # Clamp — friction shouldn't reverse the ball
        if (new_vx * self.vx < 0): new_vx = 0
        if (new_vy * self.vy < 0): new_vy = 0

        # Position uses new velocity
        new_x = self.x + new_vx * dt
        new_y = self.y + new_vy * dt

        self.body.velocity = (new_vx, new_vy)
        self.body.position = (new_x,  new_y)

    # Draw the ball in the coressponding position
    def draw(self, surface):
        if self.alive and self.body:
            pos = self.body.position
            pygame.draw.circle(surface, self.color, (int(pos.x), int(pos.y)), self.radius)
