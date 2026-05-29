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
        return math.hypot(self.velocity.x, self.velocity.y)

    def apply_force(self, force, direction: pygame.Vector2, dt=1/60.0):
        force = max(c.MIN_FORCE, min(c.MAX_FORCE, force))

        impulse = force * dt

        length = math.hypot(direction.x, direction.y)
        if length == 0:
            return
        ux = direction.x / length
        uy = direction.y / length

        new_vx = self.velocity.x + (impulse * ux) / self.mass
        new_vy = self.velocity.y + (impulse * uy) / self.mass
        self.velocity = pygame.Vector2(new_vx, new_vy)

    def apply_friction(self, friction_coeff, dt=1/60.0):
        if not self.alive:
            return

        if self.speed < 0.5:
            self.velocity = pygame.Vector2(0, 0)
            return

        friction_force = friction_coeff * self.mass * c.GRAVITY

        ux = -self.velocity.x / self.speed
        uy = -self.velocity.y / self.speed

        ax = (friction_force * ux) / self.mass
        ay = (friction_force * uy) / self.mass

        new_vx = self.velocity.x + ax * dt
        new_vy = self.velocity.y + ay * dt

        if (new_vx * self.velocity.x < 0): new_vx = 0
        if (new_vy * self.velocity.y < 0): new_vy = 0

        new_x = self.position.x + new_vx * dt
        new_y = self.position.y + new_vy * dt

        self.velocity = pygame.Vector2(new_vx, new_vy)
        self.position = pygame.Vector2(new_x, new_y)
        self.shape["center"] = self.position

    def update(self, dt):
        if not self.alive:
            return
        self.apply_friction(c.BALL_FRICTION, dt)

    def draw(self, surface):
        if self.alive:
            pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), int(self.radius))
