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

    # TODO: STILL NEED REWORK!
    def draw(self, surface):
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
        
        # Draw the corner pockets
        # Using c.CORNER_POCKET_LENGTH for size
        pocket_master = pygame.Surface((c.CORNER_POCKET_LENGTH, c.CORNER_POCKET_LENGTH), pygame.SRCALPHA)
        pygame.draw.rect(pocket_master, (0, 0, 0), (0, 0, c.CORNER_POCKET_LENGTH, c.CORNER_POCKET_LENGTH))

        offset = (c.CORNER_POCKET_LENGTH // 2) + 28
        
        # Positions use your MARGIN and SCREEN size constants
        corners = [
            {"angle": 45,  "pos": (c.MARGIN + offset, c.MARGIN + offset)},                          # Top-Left (In and Down)
            {"angle": -45, "pos": (c.SCREEN_W - c.MARGIN - offset, c.MARGIN + offset)},             # Top-Right (In and Down)
            {"angle": 135, "pos": (c.MARGIN + offset, c.SCREEN_H - c.MARGIN - offset)},             # Bottom-Left (In and Up)
            {"angle": 225, "pos": (c.SCREEN_W - c.MARGIN - offset, c.SCREEN_H - c.MARGIN - offset)} # Bottom-Right (In and Up)
        ]

        # Rotate and blit for each corner
        for corner in corners:
            # Rotate the master square
            rotated_surf = pygame.transform.rotate(pocket_master, corner["angle"])
            
            # Get a new rect centered exactly on the corner coordinate
            # This prevents the pocket from shifting due to the rotation's size increase
            rect = rotated_surf.get_rect(center=corner["pos"])
            
            # Draw it to your target surface
            surface.blit(rotated_surf, rect.topleft)

        # Draw side pockets
        # 1. Create the master surface for the side pockets
        side_pocket_master = pygame.Surface((c.SIDE_POCKET_LENGTH, c.SIDE_POCKET_LENGTH), pygame.SRCALPHA)
        pygame.draw.rect(side_pocket_master, (0, 0, 0), (0, 0, c.SIDE_POCKET_LENGTH, c.SIDE_POCKET_LENGTH))

        # 2. Set the offset (how deep into the table they sit)
        # Adjust this value to line it up with your cushions
        side_offset = (c.SIDE_POCKET_LENGTH // 2) -1

        # 3. Define the positions for the two middle pockets
        # X is exactly in the middle of the screen
        # Y is at the margins plus/minus the offset
        side_pockets = [
            {"angle": 0, "pos": (c.SCREEN_W // 2, c.MARGIN + side_offset)},               # Top Middle
            {"angle": 0, "pos": (c.SCREEN_W // 2, c.SCREEN_H - c.MARGIN - side_offset)}  # Bottom Middle
        ]

        # 4. Draw them
        for pocket in side_pockets:
            # Even if angle is 0, we use the same blit logic for consistency
            rotated_surf = pygame.transform.rotate(side_pocket_master, pocket["angle"])
            rect = rotated_surf.get_rect(center=pocket["pos"])
            surface.blit(rotated_surf, rect.topleft)