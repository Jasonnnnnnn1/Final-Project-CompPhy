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

        # pocketed balls array
        self.pocketed = []

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
            "length": c.SIDE_POCKET_LENGTH,
            "angle": 0,
            "is_corner": False
        })
        defs.append({
            "rect": pygame.Rect(cx - half_s, self.play_bottom,
                                c.SIDE_POCKET_LENGTH, c.SIDE_POCKET_LENGTH),
            "center": (cx, self.play_bottom + half_s),
            "length": c.SIDE_POCKET_LENGTH,
            "angle": 0,
            "is_corner": False
        })

        # Corner pockets: Precise quadrant vectors
        # Format: (mouth_x, mouth_y, dx, dy, angle)
        corners = [
            (self.play_left,  self.play_top,    -1, -1, 45),   # Top-Left
            (self.play_right, self.play_top,     1, -1, -45),  # Top-Right
            (self.play_left,  self.play_bottom, -1,  1, 135),  # Bottom-Left
            (self.play_right, self.play_bottom,  1,  1, 225),  # Bottom-Right
        ]
        for mouth_x, mouth_y, dx, dy, angle in corners:
            # Shift the center slightly inward toward the playable table surface
            # to make sure the square completely covers the cushion corner apex.
            center_x = mouth_x + (dx * (half_c * 0.06))  
            center_y = mouth_y + (dy * (half_c * 0.06))  

            # Expand detection size slightly to catch fast moving balls safely
            detection_size = int(c.CORNER_POCKET_LENGTH * 1.3)
            rect = pygame.Rect(0, 0, detection_size, detection_size)
            rect.center = (int(center_x), int(center_y))
            
            defs.append({
                "rect": rect,
                "center": (center_x, center_y),
                "length": c.CORNER_POCKET_LENGTH,
                "angle": angle,
                "is_corner": True
            })

        return defs

    # Open the cushion boundaries to make the ball hit the pocket openings
    def is_top_cushion_open(self, ball):
        if abs(ball.x - c.SCREEN_W // 2) <= c.SIDE_POCKET_LENGTH // 2:
            return True
        if ball.x < self.play_left + (c.CORNER_POCKET_LENGTH * 0.5):
            return True
        if ball.x > self.play_right - (c.CORNER_POCKET_LENGTH * 0.5):
            return True
        return False

    def is_bottom_cushion_open(self, ball):
        return self.is_top_cushion_open(ball)

    def is_left_cushion_open(self, ball):
        if ball.y < self.play_top + (c.CORNER_POCKET_LENGTH * 0.5):
            return True
        if ball.y > self.play_bottom - (c.CORNER_POCKET_LENGTH * 0.5):
            return True
        return False

    def is_right_cushion_open(self, ball):
        return self.is_left_cushion_open(ball)

    def _ball_overlaps_pocket(self, ball, pocket):
        dx = ball.x - pocket["center"][0]
        dy = ball.y - pocket["center"][1]
        distance_squared = dx * dx + dy * dy
        
        # 0.50 = The pocket drop radius is exactly half its full width.
        # Make the value higher for larger hitbox radius, make it smaller for a smaller hitbox radius
        hitbox_strictness = 0.55
        
        drop_radius = pocket["length"] * hitbox_strictness
        
        # Check if the ball's center has crossed into the inner drop radius
        return distance_squared <= drop_radius * drop_radius

    def check_pockets(self, balls):
        newly_pocketed = []
        
        for ball in balls:
            if not ball.alive:
                continue
                
            for pocket in self.pocket_defs:
                if self._ball_overlaps_pocket(ball, pocket):
                    # Kill ANY ball that enters a pocket, including the cue ball
                    ball.alive = False
                    ball.velocity = pygame.Vector2(0, 0)
                    ball.angular_velocity = 0.0
                    
                    if getattr(ball, 'is_cue', False): 
                        print("Cue ball is pocketed (Scratch!)")
                    else:
                        self.pocketed.append(ball)
                        
                    newly_pocketed.append(ball)
                    break # Break out of the pocket loop for this ball
                    
        return newly_pocketed

    def draw(self, surface):
        # 1. Base wood rail border
        table_rect = pygame.Rect(self.left, self.top, c.SCREEN_TABLE_W, c.SCREEN_TABLE_H)
        pygame.draw.rect(surface, (60, 40, 20), table_rect)
        
        # 2. Main green playing cloth field
        felt_rect = pygame.Rect(self.play_left, self.play_top, 
                                self.play_right - self.play_left, self.play_bottom - self.play_top)
        pygame.draw.rect(surface, (24, 100, 50), felt_rect)

        # 3. Render green linear table cushions
        cushion_color = (15, 70, 35)

        # Top Cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.play_left, self.play_top - c.CUSHION_WIDTH,
                        self.play_right - self.play_left, c.CUSHION_WIDTH))
        # Bottom Cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.play_left, self.play_bottom,
                        self.play_right - self.play_left, c.CUSHION_WIDTH))
        # Left Cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.play_left - c.CUSHION_WIDTH, self.play_top,
                        c.CUSHION_WIDTH, self.play_bottom - self.play_top))
        # Right Cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.play_right, self.play_top,
                        c.CUSHION_WIDTH, self.play_bottom - self.play_top))

        # 4. Draw pockets LAST to cleanly cut out mouths over the cushions
        for pocket in self.pocket_defs:
            size = pocket["length"]
            
            # Create transparent surface matching the base pocket size
            master = pygame.Surface((size, size), pygame.SRCALPHA)
            
            if pocket["is_corner"]:
                # Draw a sharp square fill for the corner holes
                pygame.draw.rect(master, (10, 12, 15), (0, 0, size, size))
                # Rotate the surface by 45 degrees
                rotated = pygame.transform.rotate(master, 45)
            else:
                # Keep side pockets rectangular
                pygame.draw.rect(master, (10, 12, 15), (0, 0, size, size))
                rotated = master

            # Force Pygame to position the surface relative to its absolute geometric center
            rect = rotated.get_rect(center=(int(pocket["center"][0]), int(pocket["center"][1])))
            surface.blit(rotated, rect.topleft)
