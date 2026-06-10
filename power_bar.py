import pygame
import constants as c

class PowerBar:
    def __init__(self):
        self.force = c.INIT_FORCE
        self.min_f = c.MIN_FORCE
        self.max_f = c.MAX_FORCE

    @property
    def t(self):
        # Normalised value 0-1 representing force position in the range
        # Used to map force to a heatmap color and bar fill height
        return (self.force - self.min_f) / (self.max_f - self.min_f)

    def increase(self, amount=50.0):
        # Increases force by amount, clamped to max force
        self.force = min(self.max_f, self.force + amount)

    def decrease(self, amount=50.0):
        # Decreases force by amount, clamped to min force
        self.force = max(self.min_f, self.force - amount)

    def set_from_mouse(self, my, bar_top, bar_height):
        # Sets force by dragging on the bar
        # my is the mouse y position, mapped to force range
        rel = my - bar_top
        t = 1.0 - max(0.0, min(1.0, rel / bar_height))
        self.force = self.min_f + t * (self.max_f - self.min_f)

    def heat_color(self):
        # Returns an RGB color based on current force level
        # Blue = low force, red = high force
        stops = [
            (0.00, (0,   0, 255)),
            (0.25, (0, 220, 255)),
            (0.50, (0, 220,   0)),
            (0.75, (255,220,  0)),
            (1.00, (255,  0,  0)),
        ]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if self.t <= t1:
                f = (self.t - t0) / (t1 - t0)
                return tuple(int(c0[j] + f * (c1[j] - c0[j])) for j in range(3))
        return stops[-1][1]

    def draw(self, surface, x, y, width, height):
        # Draws the heatmap power bar at the given position and size
        # Fills from bottom up based on current force level
        # Also draws + and - buttons and the force readout

        btn_h   = 30   # Height of + and - buttons
        bar_rec = pygame.Rect(x, y + btn_h + 8, width, height)

        # Bar background
        pygame.draw.rect(surface, (10, 12, 16), bar_rec, border_radius=6)

        # Gradient fill from bottom up
        fill_h = int(self.t * bar_rec.height)
        for i in range(fill_h):
            t_i = i / bar_rec.height
            # Interpolate color at this strip
            col = self._color_at(t_i)
            py  = bar_rec.bottom - i - 1
            pygame.draw.line(surface, col,
                            (bar_rec.left,  py),
                            (bar_rec.right, py))

        # Marker line at current force level
        marker_y = bar_rec.bottom - fill_h
        pygame.draw.line(surface, (255, 255, 255),
                        (bar_rec.left  - 3, marker_y),
                        (bar_rec.right + 3, marker_y), 2)

        pygame.draw.rect(surface, (50, 60, 75), bar_rec, 1, border_radius=6)

        # + button above bar
        btn_plus = pygame.Rect(x, y, width, btn_h)
        pygame.draw.rect(surface, (40, 50, 65), btn_plus, border_radius=6)

        # - button below bar
        btn_minus = pygame.Rect(x, y + btn_h + height + 16, width, btn_h)
        pygame.draw.rect(surface, (40, 50, 65), btn_minus, border_radius=6)

        # Force readout in Newtons below the minus button
        font  = pygame.font.SysFont("monospace", 14)
        f_txt = font.render(f"{self.force:.0f} N", True, self.heat_color())
        surface.blit(f_txt, (x, btn_minus.bottom + 8))

    def _color_at(self, t):
        # Returns an RGB color for a given normalised t value 0-1
        # Used internally by draw to render the gradient strip by strip
        stops = [
            (0.00, (0,   0, 255)),
            (0.25, (0, 220, 255)),
            (0.50, (0, 220,   0)),
            (0.75, (255,220,  0)),
            (1.00, (255,  0,  0)),
        ]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t <= t1:
                f = (t - t0) / (t1 - t0)
                return tuple(int(c0[j] + f * (c1[j] - c0[j])) for j in range(3))
        return stops[-1][1]