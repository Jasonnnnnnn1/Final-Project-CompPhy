import pygame
import constants as c
from ball import Ball
from table import Table
from cue_stick import CueStick
from collisions import resolve_ball_collisions
from ghost_ball import draw_ghost_indicator, get_ghost_aim

def create_balls(layout):
    balls = []
    for spec in layout:
        balls.append(
            Ball(
                x_px=spec["x"],             
                y_px=spec["y"],             
                radius_m=c.BALL_RADIUS_M,   
                mass=c.BALL_MASS,
                color=spec["color"],
                is_cue=spec.get("is_cue", False),
                is_black=spec.get("is_black", False),
                image_path=spec.get("img", None) 
            )
        )
    return balls


def reset_game(balls, cue_stick, layout):
    # Reset all ball physics properties safely
    for ball, spec in zip(balls, layout):
        ball.alive = True
        ball.x = spec["x"] 
        ball.y = spec["y"]
        ball.velocity = pygame.Vector2(0, 0)
        ball.angular_velocity = 0.0
        
    # Reset the cue stick object states completely
    cue_stick.active = True
    if hasattr(cue_stick, 'is_shooting'):
        cue_stick.is_shooting = False  # Clear any active hit animations
    
    # Reset the power bar settings
    cue_stick.power_bar.force = c.INIT_FORCE


def resolve_wall_collisions(balls, table):
    # Establish the explicit boundary lines of the cushions in pixels
    # This prevents calculations from drifting if constants are updated
    cushion_top    = table.top + c.RAIL_W
    cushion_bottom = table.bottom - c.RAIL_W
    cushion_left   = table.left + c.RAIL_W
    cushion_right  = table.right - c.RAIL_W

    for ball in balls:
        if not ball.alive:
            continue

        radius = ball.radius_px

        # --- TOP CUSHION ---
        if ball.y - radius < cushion_top:
            if not table.is_top_cushion_open(ball):
                # Ensure the ball is heading TOWARDS the cushion before bouncing
                if ball.vy < 0:
                    ball.y = cushion_top + radius
                    ball.vy *= -c.CUSHION_RESTITUTION

        # --- BOTTOM CUSHION ---
        elif ball.y + radius > cushion_bottom:
            if not table.is_bottom_cushion_open(ball):
                if ball.vy > 0:
                    ball.y = cushion_bottom - radius
                    ball.vy *= -c.CUSHION_RESTITUTION

        # --- LEFT CUSHION ---
        if ball.x - radius < cushion_left:
            if not table.is_left_cushion_open(ball):
                if ball.vx < 0:
                    ball.x = cushion_left + radius
                    ball.vx *= -c.CUSHION_RESTITUTION

        # --- RIGHT CUSHION ---
        elif ball.x + radius > cushion_right:
            if not table.is_right_cushion_open(ball):
                if ball.vx > 0:
                    ball.x = cushion_right - radius
                    ball.vx *= -c.CUSHION_RESTITUTION


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    pygame.display.set_caption("BL FOR LIFE")
    clock = pygame.time.Clock()

    table = Table()
    balls = create_balls(c.INITIAL_LAYOUT)
    cue_ball = balls[0]
    black_ball = balls[5]
    cue_stick = CueStick(cue_ball)

    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    cue_stick.shoot()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    cue_stick.power_bar.increase()
                if event.key == pygame.K_DOWN:
                    cue_stick.power_bar.decrease()
                if event.key == pygame.K_r:
                    reset_game(balls, cue_stick, c.INITIAL_LAYOUT)

        mouse_pos = pygame.mouse.get_pos()
        cue_stick.update(mouse_pos)

        for ball in balls:
            ball.update(dt)

        resolve_ball_collisions(balls)
        resolve_wall_collisions(balls, table)

        table.check_pockets(balls)

        all_stopped = all(not b.alive or b.speed < 0.001 for b in balls)
        if all_stopped:
            # Check if the black ball is pocketed
            if not black_ball.alive:
                print("8-Ball is IN!")
                reset_game(balls, cue_stick, c.INITIAL_LAYOUT)
            # Check if the cue ball is pocketed
            if not cue_ball.alive:
                print("Respawning cue ball!")
                # Dynamic calculations matching table layout metrics
                playable_length = table.play_right - table.play_left
                center_y = table.play_top + (table.play_bottom - table.play_top) // 2
                cue_ball.x = table.play_left + int(playable_length * 0.25)
                cue_ball.y = center_y
                cue_ball.velocity = pygame.Vector2(0, 0)
                cue_ball.angular_velocity = 0.0
                cue_ball.alive = True
            
            # Bring cue stick back
            cue_stick.active = True

        screen.fill((15, 20, 25))
        table.draw(screen)

        for ball in balls:
            ball.draw(screen)

        ghost_visible = False
        if cue_stick.active and cue_ball.alive:
            ghost_visible = get_ghost_aim(cue_ball, balls, mouse_pos, cue_stick.direction) is not None
            draw_ghost_indicator(screen, cue_ball, balls, mouse_pos, cue_stick.direction)

        cue_stick.draw(screen, show_power_aim=not ghost_visible)

        bar_width = 40
        bar_height = c.SCREEN_TABLE_H - 40
        bar_x = (c.MARGIN - bar_width) // 2
        bar_y = c.MARGIN + 20
        cue_stick.power_bar.draw(screen, x=bar_x, y=bar_y, width=bar_width, height=bar_height)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
