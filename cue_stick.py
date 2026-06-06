import math
import pygame
import constants as c
from power_bar import PowerBar
class CueStick:
    def __init__(self, cue_ball):
        self.cue_ball = cue_ball
        self.power_bar = PowerBar()
        self.stick_length = 200
        self.offset = 20
        self.angle = 0.0
        self.active = True

    @property
    def direction(self):
        return pygame.Vector2(
            math.cos(self.angle),
            math.sin(self.angle)
        )

    def update(self, mouse_pos):
        if not self.active:
            return
        dx = self.cue_ball.x - mouse_pos[0]
        dy = self.cue_ball.y - mouse_pos[1]
        self.angle = math.atan2(dy, dx)

    def shoot(self):
        if not self.active:
            return
        self.cue_ball.apply_force(self.power_bar.force, self.direction)
        self.active = False

    def draw(self, surface, show_power_aim=True):
        if not self.active:
            return

        bx, by = self.cue_ball.x, self.cue_ball.y
        ux = math.cos(self.angle)
        uy = math.sin(self.angle)

        start_x = bx - ux * (self.cue_ball.radius + self.offset)
        start_y = by - uy * (self.cue_ball.radius + self.offset)
        end_x   = start_x - ux * self.stick_length
        end_y   = start_y - uy * self.stick_length

        pygame.draw.line(surface, (139, 90, 40),
                    (int(start_x), int(start_y)),
                    (int(end_x),   int(end_y)), 6)

        if show_power_aim:
            self._draw_aim_line(surface, bx, by, ux, uy)

    def _draw_aim_line(self, surface, bx, by, ux, uy):
        col = self.power_bar.heat_color()
        for i in range(8):
            sx = bx + ux * (i * 20 + 5)
            sy = by + uy * (i * 20 + 5)
            ex = bx + ux * (i * 20 + 15)
            ey = by + uy * (i * 20 + 15)
            pygame.draw.line(surface, col,
                            (int(sx), int(sy)),
                            (int(ex), int(ey)), 2)
