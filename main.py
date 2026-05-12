import pygame
import math
import constants as c
from ball import Ball
from table import Table
from cue_stick import CueStick

def main():
    pygame.init()
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    pygame.display.set_caption("BL FOR LIFE")
    clock  = pygame.time.Clock()

    # ── Setup ────────────────────────────────────────────────
    table     = Table()
    cue_ball  = Ball(400, 300, c.BALL_RADIUS, c.BALL_MASS, (240, 240, 240), is_cue=True)
    balls     = [
        cue_ball,
        Ball(700, 300, c.BALL_RADIUS, c.BALL_MASS, (230, 30, 30)),
        Ball(730, 285, c.BALL_RADIUS, c.BALL_MASS, (240, 200, 30)),
        Ball(730, 315, c.BALL_RADIUS, c.BALL_MASS, (40, 100, 220)),
        Ball(760, 300, c.BALL_RADIUS, c.BALL_MASS, (130, 40, 170)),
        Ball(760, 330, c.BALL_RADIUS, c.BALL_MASS, (20, 150, 80)),
    ]
    cue_stick = CueStick(cue_ball)

    # ── Game loop ────────────────────────────────────────────
    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0  # delta time in seconds

        # ── Events ───────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:   # left click to shoot
                    cue_stick.shoot()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    cue_stick.power_bar.increase()
                if event.key == pygame.K_DOWN:
                    cue_stick.power_bar.decrease()

        # ── Update ───────────────────────────────────────────
        mouse_pos = pygame.mouse.get_pos()
        cue_stick.update(mouse_pos)

        for ball in balls:
            ball.update(dt)

        # After updating ball position, check for cushion collisions
        for ball in balls:
            # Check top cushion
            if ball.y - ball.radius < table.top + c.RAIL_W:
                ball.y = table.top + c.RAIL_W + ball.radius  # Push ball back out
                ball.vy *= -c.CUSHION_RESTITUTION  # Reverse and dampen
            
            # Check bottom cushion
            if ball.y + ball.radius > table.bottom - c.RAIL_W:
                ball.y = table.bottom - c.RAIL_W - ball.radius
                ball.vy *= -c.CUSHION_RESTITUTION
            
            # Check left cushion
            if ball.x - ball.radius < table.left + c.RAIL_W:
                ball.x = table.left + c.RAIL_W + ball.radius
                ball.vx *= -c.CUSHION_RESTITUTION
            
            # Check right cushion
            if ball.x + ball.radius > table.right - c.RAIL_W:
                ball.x = table.right - c.RAIL_W - ball.radius
                ball.vx *= -c.CUSHION_RESTITUTION

        # Check if all balls stopped, re-enable cue stick
        all_stopped = all(b.speed < 0.5 for b in balls)
        if all_stopped:
            cue_stick.active = True

        # Check pockets
        pocketed = table.check_pockets(balls)

        # Draw the screen
        screen.fill((15, 20, 25))
        table.draw(screen)

        for ball in balls:
            ball.draw(screen)

        cue_stick.draw(screen)

        # Draw power bar centered in left margin so it doesn't overlap the table
        bar_width = 40
        # Fit the bar inside the top/bottom margins (give a little vertical padding)
        bar_height = c.SCREEN_TABLE_H - 40
        bar_x = (c.MARGIN - bar_width) // 2
        bar_y = c.MARGIN + 20
        cue_stick.power_bar.draw(screen, x=bar_x, y=bar_y, width=bar_width, height=bar_height)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

