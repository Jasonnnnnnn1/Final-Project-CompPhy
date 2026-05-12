import constants as c
import pygame
import math

class Table:
    def __init__(self):
        self.left = c.MARGIN
        self.right = c.MARGIN + c.SCREEN_TABLE_W
        self.top = c.MARGIN 
        self.bottom = c.MARGIN + c.SCREEN_TABLE_H
        # Offset pockets inward by half rail width so they sit on the rail
        offset = c.RAIL_W // 2
        self.pockets = [
            # Top left corner pocket
            (self.left + offset, self.top + offset, c.CORNER_POCKET_LENGTH),      
            # Top right corner pocket
            (self.right - offset, self.top + offset, c.CORNER_POCKET_LENGTH),  
            # Bottom left corner pocket    
            (self.left + offset, self.bottom - offset, c.CORNER_POCKET_LENGTH),   
            # Bottom right corner pocket
            (self.right - offset, self.bottom - offset, c.CORNER_POCKET_LENGTH),
            # Top & bottom side pockets
            (self.left + c.SCREEN_TABLE_W // 2, self.top + offset, c.SIDE_POCKET_LENGTH),  
            (self.left + c.SCREEN_TABLE_W // 2, self.bottom - offset, c.SIDE_POCKET_LENGTH)  
        ]

    # A method to check if any ball object hit a pocket, this is going to be called for every frame in the game loop
    def check_pockets(self, balls):
        pocketed = []
        for ball in balls:
            if not ball.alive:
                continue
            for (px, py, pr) in self.pockets:
                dx = ball.x - px
                dy = ball.y - py
                if dx*dx + dy*dy <= pr ** 2:
                    ball.alive = False
                    pocketed.append(ball)
                    break
        return pocketed

    def draw(self, surface):
        """Draw the table: felt, rails and pockets."""
        table_rect = pygame.Rect(self.left, self.top, c.SCREEN_TABLE_W, c.SCREEN_TABLE_H)

        # Felt (play area)
        pygame.draw.rect(surface, (24, 100, 50), table_rect)

        # Rails: draw a darker border representing the cushions
        pygame.draw.rect(surface, (60, 40, 20), table_rect, width=c.RAIL_W)

        dark = (15, 10, 5)

        # Cushion areas (filled darker green)
        cushion_color = (15, 70, 35)
        cushion_offset = c.RAIL_W - c.CUSHION_WIDTH
        
        # Top cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.left + cushion_offset, self.top + cushion_offset,
                         c.SCREEN_TABLE_W - 2 * cushion_offset, c.CUSHION_WIDTH))
        
        # Bottom cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.left + cushion_offset, self.bottom - cushion_offset - c.CUSHION_WIDTH,
                         c.SCREEN_TABLE_W - 2 * cushion_offset, c.CUSHION_WIDTH))
        
        # Left cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.left + cushion_offset, self.top + cushion_offset,
                         c.CUSHION_WIDTH, c.SCREEN_TABLE_H - 2 * cushion_offset))
        
        # Right cushion
        pygame.draw.rect(surface, cushion_color,
                        (self.right - cushion_offset - c.CUSHION_WIDTH, self.top + cushion_offset,
                         c.CUSHION_WIDTH, c.SCREEN_TABLE_H - 2 * cushion_offset))
        
        # Corner pocket openings (diagonal squares with diagonal = CORNER_POCKET_LENGTH)
        delta = c.CORNER_POCKET_LENGTH // 2
        pocket_depth = delta 
        
        # Pocket 0: Top-left corner (rotated 45 degrees)
        pygame.draw.polygon(surface, dark,
                        [(self.left + c.RAIL_W - delta, self.top + c.RAIL_W),
                        (self.left + c.RAIL_W, self.top + c.RAIL_W - pocket_depth),
                        (self.left + c.RAIL_W + delta, self.top + c.RAIL_W),
                        (self.left + c.RAIL_W, self.top + c.RAIL_W + pocket_depth)])
        
        # Pocket 1: Top-right corner
        pygame.draw.polygon(surface, dark,
                        [(self.right - c.RAIL_W - delta, self.top + c.RAIL_W),
                        (self.right - c.RAIL_W, self.top + c.RAIL_W - pocket_depth),
                        (self.right - c.RAIL_W + delta, self.top + c.RAIL_W),
                        (self.right - c.RAIL_W, self.top + c.RAIL_W + pocket_depth)])
        
        # Pocket 2: Bottom-left corner
        pygame.draw.polygon(surface, dark,
                        [(self.left + c.RAIL_W - delta, self.bottom - c.RAIL_W),
                        (self.left + c.RAIL_W, self.bottom - c.RAIL_W - pocket_depth),
                        (self.left + c.RAIL_W + delta, self.bottom - c.RAIL_W),
                        (self.left + c.RAIL_W, self.bottom - c.RAIL_W + pocket_depth)])
        
        # Pocket 3: Bottom-right corner
        pygame.draw.polygon(surface, dark,
                        [(self.right - c.RAIL_W - delta, self.bottom - c.RAIL_W),
                        (self.right - c.RAIL_W, self.bottom - c.RAIL_W - pocket_depth),
                        (self.right - c.RAIL_W + delta, self.bottom - c.RAIL_W),
                        (self.right - c.RAIL_W, self.bottom - c.RAIL_W + pocket_depth)])
        
        # Side pocket openings at the inner rail edge
        # Pocket 4: Top-middle opening line (at inner rail edge)
        px, py, _ = self.pockets[4]
        opening_y = self.top + c.RAIL_W
        pygame.draw.line(surface, dark, (int(px - c.SIDE_POCKET_LENGTH // 2), int(opening_y)), 
                                       (int(px + c.SIDE_POCKET_LENGTH // 2), int(opening_y)), width=4)
        
        # Pocket 5: Bottom-middle opening line (at inner rail edge)
        px, py, _ = self.pockets[5]
        opening_y = self.bottom - c.RAIL_W
        pygame.draw.line(surface, dark, (int(px - c.SIDE_POCKET_LENGTH // 2), int(opening_y)), 
                                       (int(px + c.SIDE_POCKET_LENGTH // 2), int(opening_y)), width=4)