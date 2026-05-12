from power_bar import PowerBar
import math
import pygame

class CueStick:
    def __init__(self, cue_ball):
        self.cue_ball = cue_ball # A ball object
        self.power_bar = PowerBar() # Composition relationship
        self.stick_length = 200 # length of stick in px
        self.offset = 20 # Gap between the stick and the cue ball in px
        self.angle = 0.0 # Angle of which the cue stick is pointing to the cue ball
        self.active = True # Set to true when the state of all the balls are at rest
    
    @property
    def direction(self):
        # Unit vector pointing in the shoot direction derived from the current angle
        return pygame.Vector2(
            math.cos(self.angle),
            math.sin(self.angle)
        )

    def update(self, mouse_pos):
        # Recalculates the angle every frame based on mouse position relative to cue ball
        # Does nothing if the stick is not active
        if not self.active:
            return
        dx = self.cue_ball.x - mouse_pos[0]
        dy = self.cue_ball.y - mouse_pos[1]
        self.angle = math.atan2(dy, dx)

    def shoot(self):
        # Applies the power bar force to the cue ball in the current aim direction
        if not self.active:
            return
        self.cue_ball.apply_force(self.power_bar.force, self.direction)
        self.active = False # deactivate the stick until all balls stop moving

    def draw(self, surface):
        # Draws the cue stick behind the cue ball and the aim line in front
        if not self.active:
            return # Does nothing if the stick is not active

        bx, by = self.cue_ball.x, self.cue_ball.y
        ux = math.cos(self.angle)
        uy = math.sin(self.angle)

        # Stick sits behind the cue ball offset by radius + gap
        start_x = bx - ux * (self.cue_ball.radius + self.offset)
        start_y = by - uy * (self.cue_ball.radius + self.offset)
        end_x   = start_x - ux * self.stick_length
        end_y   = start_y - uy * self.stick_length

        pygame.draw.line(surface, (139, 90, 40),
                    (int(start_x), int(start_y)),
                    (int(end_x),   int(end_y)), 6)

        self._draw_aim_line(surface, bx, by, ux, uy)

    def _draw_aim_line(self, surface, bx, by, ux, uy):
        # Draws a dashed line in the shoot direction colored by the current force level
        # Higher force = warmer color from the power bar heatmap
        col = self.power_bar.heat_color()
        for i in range(8):
            sx = bx + ux * (i * 20 + 5)
            sy = by + uy * (i * 20 + 5)
            ex = bx + ux * (i * 20 + 15)
            ey = by + uy * (i * 20 + 15)
            pygame.draw.line(surface, col,
                            (int(sx), int(sy)),
                            (int(ex), int(ey)), 2)

