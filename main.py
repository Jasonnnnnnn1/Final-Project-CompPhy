import pygame
import constants as c
from ball import Ball
from table import Table
from cue_stick import CueStick
from collisions import resolve_ball_collisions
from ghost_ball import draw_ghost_indicator, get_ghost_aim

# Saved layout used by the R-key restart
INITIAL_LAYOUT = [
    {"x": 400, "y": 300, "color": (240, 240, 240), "is_cue": True},
    {"x": 700, "y": 300, "color": (230, 30, 30)},
    {"x": 730, "y": 285, "color": (240, 200, 30)},
    {"x": 730, "y": 315, "color": (40, 100, 220)},
    {"x": 760, "y": 300, "color": (130, 40, 170)},
    {"x": 760, "y": 330, "color": (20, 150, 80)},
]


def create_balls(layout):
    balls = []
    for spec in layout:
        balls.append(
            Ball(
                spec["x"],
                spec["y"],
                c.BALL_RADIUS,
                c.BALL_MASS,
                spec["color"],
                is_cue=spec.get("is_cue", False),
            )
        )
    return balls


def reset_game(balls, cue_stick, layout):
    for ball, spec in zip(balls, layout):
        ball.alive = True
        ball.x = spec["x"]
        ball.y = spec["y"]
        ball.velocity = pygame.Vector2(0, 0)
    cue_stick.active = True
    cue_stick.power_bar.force = c.INIT_FORCE


def resolve_wall_collisions(balls, table):
    for ball in balls:
        if not ball.alive:
            continue

        if ball.y - ball.radius < table.top + c.RAIL_W:
            if not table.is_top_cushion_open(ball):
                ball.y = table.top + c.RAIL_W + ball.radius
                ball.vy *= -c.CUSHION_RESTITUTION

        if ball.y + ball.radius > table.bottom - c.RAIL_W:
            if not table.is_bottom_cushion_open(ball):
                ball.y = table.bottom - c.RAIL_W - ball.radius
                ball.vy *= -c.CUSHION_RESTITUTION

        if ball.x - ball.radius < table.left + c.RAIL_W:
            if not table.is_left_cushion_open(ball):
                ball.x = table.left + c.RAIL_W + ball.radius
                ball.vx *= -c.CUSHION_RESTITUTION

        if ball.x + ball.radius > table.right - c.RAIL_W:
            if not table.is_right_cushion_open(ball):
                ball.x = table.right - c.RAIL_W - ball.radius
                ball.vx *= -c.CUSHION_RESTITUTION


def main():
    pygame.init()
    screen = pygame.display.set_mode((c.SCREEN_W, c.SCREEN_H))
    pygame.display.set_caption("BL FOR LIFE")
    clock = pygame.time.Clock()

    table = Table()
    balls = create_balls(INITIAL_LAYOUT)
    cue_ball = balls[0]
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
                    reset_game(balls, cue_stick, INITIAL_LAYOUT)

        mouse_pos = pygame.mouse.get_pos()
        cue_stick.update(mouse_pos)

        for ball in balls:
            ball.update(dt)

        resolve_ball_collisions(balls)
        resolve_wall_collisions(balls, table)

        all_stopped = all(not b.alive or b.speed < 0.5 for b in balls)
        if all_stopped:
            cue_stick.active = True

        table.check_pockets(balls)

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
