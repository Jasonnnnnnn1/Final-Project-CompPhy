import pygame
import math
import constants as c


class Ball:
    def __init__(self, x, y, radius, mass, color, is_cue=False):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = float(radius)
        self.mass = float(mass)
        self.color = color
        self.is_cue = is_cue
        self.alive = True
        self.shape = {
            "type": "circle",
            "radius": self.radius,
            "center": self.position,
        }

    # Get position components
    @property
    def x(self):
        return self.position.x

    @x.setter
    def x(self, v):
        self.position.x = float(v)
        self.shape["center"] = self.position

    @property
    def y(self):
        return self.position.y

    @y.setter
    def y(self, v):
        self.position.y = float(v)
        self.shape["center"] = self.position

    # Get velocity components
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
    # Get the speed of the ball (hypotenuse of both velocity components)
    @property
    def speed(self):
        return math.hypot(self.velocity.x, self.velocity.y)

    # Applying the force to the ball object
    def apply_force(self, force, direction: pygame.Vector2, dt=1/60.0):
        # Set the force to the very max or the very min even if the user keeps on adding on it
        force = max(c.MIN_FORCE, min(c.MAX_FORCE, force))

        impulse = force * dt  # KEY EQUATION: J = F * dt

        # Normalizing the direction to get the unit vectors
        length = math.hypot(direction.x, direction.y)
        if length == 0:
            return
        # UNIT components
        ux = direction.x / length
        uy = direction.y / length

        # Calculate the new velocity components from the impulse force, KEY EQUATION: v = J/m
        new_vx = self.velocity.x + (impulse * ux) / self.mass
        new_vy = self.velocity.y + (impulse * uy) / self.mass
        self.velocity = pygame.Vector2(new_vx, new_vy)

    # Apply friction to the ball for every frame
    # The semi-implicit euler method is implemented in this function
    def apply_friction(self, friction_coeff, dt=1/60.0):
        if not self.alive:
            return
        
        # Stop the ball if the speed is already very very very low
        if self.speed < 0.5:
            self.velocity = pygame.Vector2(0, 0)
            return
        
        # Frictional force acting on the ball
        friction_force = friction_coeff * self.mass * c.GRAVITY  # KEY EQUATION: f = μ * m * g

        # Calculating the unit positional component by dividing the velocity of each component by its speed
        # Then adding a minus sign since this is a decrease in velocity
        ux = -self.velocity.x / self.speed
        uy = -self.velocity.y / self.speed

        # Finding the acceleration of the ball object 
        # KEY EQUATION: a = f/m (where f is the frictional force transformed by each component, and m is mass of the object)
        ax = (friction_force * ux) / self.mass
        ay = (friction_force * uy) / self.mass

        # Calculating the new/predicted velocity first 
        # KEY EQUATION: v(n+1) = v(n) + a*dt
        new_vx = self.velocity.x + ax * dt
        new_vy = self.velocity.y + ay * dt

        # Stop the frictional force in rolling the ball backwards
        if (new_vx * self.velocity.x < 0): new_vx = 0
        if (new_vy * self.velocity.y < 0): new_vy = 0

        # SEMI-IMPLICIT Euler method: uses the just computed velocity to calculate the position of the ball
        # KEY EQUATION: r(n+1) = r(n) + v(n+1)*dt
        new_x = self.position.x + new_vx * dt
        new_y = self.position.y + new_vy * dt

        # Update both the velocity and position vectors
        self.velocity = pygame.Vector2(new_vx, new_vy)
        self.position = pygame.Vector2(new_x, new_y)
        self.shape["center"] = self.position

    def update(self, dt):
        if not self.alive:
            return
        self.apply_friction(c.BALL_FRICTION, dt)

    # Draw the ball in its corresponding position
    def draw(self, surface):
        if self.alive:
            pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), int(self.radius))
