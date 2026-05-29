import constants as c
import pygame


class Table:
    def __init__(self):
        self.left = c.MARGIN
        self.right = c.MARGIN + c.SCREEN_TABLE_W
        self.top = c.MARGIN
        self.bottom = c.MARGIN + c.SCREEN_TABLE_H

        # Inner edge of the playing surface (inside the rails)
        self.play_left = self.left + c.RAIL_W
        self.play_right = self.right - c.RAIL_W
        self.play_top = self.top + c.RAIL_W
        self.play_bottom = self.bottom - c.RAIL_W

        self.pocket_defs = self._build_pocket_defs()

    def _build_pocket_defs(self):
        """Pocket rects aligned to the play-area lip; black holes sit in the rails."""
        defs = []
        half_s = c.SIDE_POCKET_LENGTH // 2
        half_c = c.CORNER_POCKET_LENGTH // 2
        cx = c.SCREEN_W // 2

        # Side pockets: mouth flush with play_top / play_bottom, black extends into rail
        defs.append({
            "rect": pygame.Rect(cx - half_s, self.play_top - c.SIDE_POCKET_LENGTH,
                               c.SIDE_POCKET_LENGTH, c.SIDE_POCKET_LENGTH),
            "center": (cx, self.play_top - half_s),
            "size": c.SIDE_POCKET_LENGTH,
            "angle": 0,
        })
        defs.append({
            "rect": pygame.Rect(cx - half_s, self.play_bottom,
                               c.SIDE_POCKET_LENGTH, c.SIDE_POCKET_LENGTH),
            "center": (cx, self.play_bottom + half_s),
            "size": c.SIDE_POCKET_LENGTH,
            "angle": 0,
        })

        # Corner pockets: mouth at play corner, square extends into margin
        corners = [
            (self.play_left, self.play_top, 45),
            (self.play_right, self.play_top, -45),
            (self.play_left, self.play_bottom, 135),
            (self.play_right, self.play_bottom, 225),
        ]
        for mouth_x, mouth_y, angle in corners:
            if angle in (45, 135):
                center_x = mouth_x - half_c
            else:
                center_x = mouth_x + half_c
            if angle in (45, -45):
                center_y = mouth_y - half_c
            else:
                center_y = mouth_y + half_c

            rect = pygame.Rect(0, 0, c.CORNER_POCKET_LENGTH, c.CORNER_POCKET_LENGTH)
            rect.center = (int(center_x), int(center_y))
            defs.append({
                "rect": rect,
                "center": (center_x, center_y),
                "size": c.CORNER_POCKET_LENGTH,
                "angle": angle,
            })

        return defs

    def is_top_cushion_open(self, ball):
        if abs(ball.x - c.SCREEN_W // 2) <= c.SIDE_POCKET_LENGTH // 2:
            return True
        if ball.x < self.play_left + c.CORNER_POCKET_LENGTH:
            return True
        if ball.x > self.play_right - c.CORNER_POCKET_LENGTH:
            return True
        return False

    def is_bottom_cushion_open(self, ball):
        return self.is_top_cushion_open(ball)

    def is_left_cushion_open(self, ball):
        if ball.y < self.play_top + c.CORNER_POCKET_LENGTH:
            return True
        if ball.y > self.play_bottom - c.CORNER_POCKET_LENGTH:
            return True
        return False

    def is_right_cushion_open(self, ball):
        return self.is_left_cushion_open(ball)

    def _ball_overlaps_rect(self, ball, rect):
        """True when the ball touches the pocket rectangle (matches black hole art)."""
        closest_x = max(rect.left, min(ball.x, rect.right))
        closest_y = max(rect.top, min(ball.y, rect.bottom))
        dx = ball.x - closest_x
        dy = ball.y - closest_y
        return dx * dx + dy * dy <= ball.radius * ball.radius

    def check_pockets(self, balls):
        pocketed = []
        for ball in balls:
            if not ball.alive:
                continue
            for pocket in self.pocket_defs:
                if self._ball_overlaps_rect(ball, pocket["rect"]):
                    ball.alive = False
                    ball.velocity = pygame.Vector2(0, 0)
                    pocketed.append(ball)
                    break
        return pocketed

    def draw(self, surface):
        table_rect = pygame.Rect(self.left, self.top, c.SCREEN_TABLE_W, c.SCREEN_TABLE_H)

        pygame.draw.rect(surface, (24, 100, 50), table_rect)
        pygame.draw.rect(surface, (60, 40, 20), table_rect, width=c.RAIL_W)

        cushion_color = (15, 70, 35)
        cushion_offset = c.RAIL_W - c.CUSHION_WIDTH

        pygame.draw.rect(surface, cushion_color,
                        (self.left + cushion_offset, self.top + cushion_offset,
                         c.SCREEN_TABLE_W - 2 * cushion_offset, c.CUSHION_WIDTH))

        pygame.draw.rect(surface, cushion_color,
                        (self.left + cushion_offset, self.bottom - cushion_offset - c.CUSHION_WIDTH,
                         c.SCREEN_TABLE_W - 2 * cushion_offset, c.CUSHION_WIDTH))

        pygame.draw.rect(surface, cushion_color,
                        (self.left + cushion_offset, self.top + cushion_offset,
                         c.CUSHION_WIDTH, c.SCREEN_TABLE_H - 2 * cushion_offset))

        pygame.draw.rect(surface, cushion_color,
                        (self.right - cushion_offset - c.CUSHION_WIDTH, self.top + cushion_offset,
                         c.CUSHION_WIDTH, c.SCREEN_TABLE_H - 2 * cushion_offset))

        for pocket in self.pocket_defs:
            size = pocket["size"]
            master = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(master, (0, 0, 0), (0, 0, size, size))
            rotated = pygame.transform.rotate(master, pocket["angle"])
            rect = rotated.get_rect(center=(int(pocket["center"][0]), int(pocket["center"][1])))
            surface.blit(rotated, rect.topleft)
