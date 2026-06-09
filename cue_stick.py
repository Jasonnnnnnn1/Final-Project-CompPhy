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
        # Convert angle to a unit vector of the direction
        # EQUATIONS: ux = cos(angle),  uy = sin(angle)
        return pygame.Vector2(
            math.cos(self.angle),
            math.sin(self.angle)
        )

    def update(self, mouse_pos):
        if not self.active:
            return
        # Vector from mouse to ball, so the stick points away from the mouse
        dx = self.cue_ball.x - mouse_pos[0]
        dy = self.cue_ball.y - mouse_pos[1]
        # Get the angle using antitan
        # EQUATIONS: angle = atan2(dy, dx) 
        self.angle = math.atan2(dy, dx)

    def shoot(self):
        if not self.active:
            return
        # Apply force to the cue ball, using the apply_force method in the ball object
        self.cue_ball.apply_force(self.power_bar.force, self.direction)
        # Deactivate the stick
        self.active = False

    def draw(self, surface, show_power_aim=True):
        if not self.active:
            return

        # Grab ball center in pixel coords
        bx, by = self.cue_ball.x, self.cue_ball.y
        # Unit vector pointing along the stick direction
        ux = math.cos(self.angle)
        uy = math.sin(self.angle)

        # Start of the stick = ball surface + offset gap, going backward from ball
        # EQUATIONS: start = ball_center - unit_dir * (radius + offset)
        start_x = bx - ux * (self.cue_ball.radius_px + self.offset)
        start_y = by - uy * (self.cue_ball.radius_px + self.offset)
        # End of the stick = walk further back by stick_length
        # EQUATIONS: end = start - unit_dir * stick_length
        end_x   = start_x - ux * self.stick_length
        end_y   = start_y - uy * self.stick_length

        pygame.draw.line(surface, (139, 90, 40),
                    (int(start_x), int(start_y)),
                    (int(end_x),   int(end_y)), 6)

        if show_power_aim:
            self._draw_aim_line(surface, bx, by, ux, uy)

    def _draw_aim_line(self, surface, bx, by, ux, uy):
        # Color shifts with power level, hotter color = more force
        col = self.power_bar.heat_color()
        # Draw 8 dashed segments along the aim direction in front of the ball
        for i in range(8):
            # EQUATIONS: segment_start = ball_center + unit_dir * (i * spacing + dash_start)
            sx = bx + ux * (i * 20 + 5)
            sy = by + uy * (i * 20 + 5)
            # EQUATIONS: segment_end = ball_center + unit_dir * (i * spacing + dash_end)
            ex = bx + ux * (i * 20 + 15)
            ey = by + uy * (i * 20 + 15)
            pygame.draw.line(surface, col,
                            (int(sx), int(sy)),
                            (int(ex), int(ey)), 2)