import pygame
import random
import sys
import os

pygame.init()

WIDTH, HEIGHT = 800, 600
TITLE = "Animal Escape"
FPS = 60
PLAYER_SIZE = ENEMY_SIZE = 60
ITEM_SIZE = 30
OBSTACLE_SIZE = 50
HISTORY_LIMIT = 30
HIGH_SCORE_FILE = "high_score.txt"
BOOST_DURATION = 15000
NORMAL_SPEED = 5
BOOST_SPEED = 8

BG_COLOR = (214, 251, 228)
CARROT_COLOR = (255, 200, 150)
APPLE_COLOR = (255, 182, 193)
POISON_COLOR = (216, 191, 216)
BUSH_COLOR = (200, 220, 200)
HUD_COLOR = (100, 100, 120)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

is_fullscreen = False
original_size = (WIDTH, HEIGHT)


def create_window():
    global screen, WIDTH, HEIGHT
    if is_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        WIDTH, HEIGHT = screen.get_size()
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)


create_window()
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
title_font = pygame.font.SysFont(None, 72)
option_font = pygame.font.SysFont(None, 28)


def load_image(name, size=None):
    path = os.path.join(ASSETS_DIR, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception as e:
        print(f"Warning: Could not load {name}: {e}")
        return None


icon = load_image("stefanek.png")
if icon:
    pygame.display.set_icon(icon)
default_player = load_image("stefanek-pic.png", (PLAYER_SIZE, PLAYER_SIZE))
chunkier_sprites = [load_image(f"chunkier-stefanek-pic-{i}.png", (PLAYER_SIZE, PLAYER_SIZE)) for i in range(6)]
enemy_sprite = load_image("pirat.png", (ENEMY_SIZE, ENEMY_SIZE))
carrot_sprite = load_image("carrot.png", (ITEM_SIZE, ITEM_SIZE))
apple_sprite = load_image("golden-apple.webp", (ITEM_SIZE, ITEM_SIZE))
poison_sprite = load_image("poison.png", (ITEM_SIZE, ITEM_SIZE))
bush_sprite = load_image("bush.png", (OBSTACLE_SIZE, OBSTACLE_SIZE))
angel_sprite = load_image("angel-stefanek.png", (PLAYER_SIZE, PLAYER_SIZE))


def animate_fly_to_heaven(start_pos):
    if not angel_sprite:
        return
    x, y = start_pos
    total_frames = FPS * 2
    dy = -(y + PLAYER_SIZE) / total_frames
    for _ in range(int(total_frames)):
        clock.tick(FPS)
        screen.fill(BG_COLOR)
        screen.blit(angel_sprite, (x, y))
        pygame.display.flip()
        y += dy


def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            return int(f.read())
    except:
        return 0


def save_high_score(score):
    with open(HIGH_SCORE_FILE, 'w') as f:
        f.write(str(score))


def get_difficulty_settings(level):
    return {"Easy": (3, 1), "Medium": (5, 2), "Hard": (7, 3)}.get(level, (3, 1))


def draw_text_centered(text, y_offset=0, color=HUD_COLOR):
    surf = font.render(text, True, color)
    x = (WIDTH - surf.get_width()) // 2
    y = (HEIGHT - surf.get_height()) // 2 + y_offset
    screen.blit(surf, (x, y))


def draw_start_screen(selected):
    screen.fill(BG_COLOR)
    title_surf = title_font.render('Stefanek in trouble', True, (255, 182, 193))
    title_x = (WIDTH - title_surf.get_width()) // 2
    title_y = (HEIGHT - title_surf.get_height()) // 2 - 130
    screen.blit(title_surf, (title_x, title_y))
    opt_surf = option_font.render('Select Difficulty: [1]Easy [2]Medium [3]Hard', True, (225, 105, 180))
    opt_x = (WIDTH - opt_surf.get_width()) // 2
    opt_y = title_y + 130
    screen.blit(opt_surf, (opt_x, opt_y))
    curr_surf = option_font.render(f'Current: {selected}', True, (225, 105, 180))
    screen.blit(curr_surf, ((WIDTH - curr_surf.get_width()) // 2, opt_y + 40))
    help_surf = option_font.render('Press I for Instructions', True, (225, 105, 180))
    screen.blit(help_surf, ((WIDTH - help_surf.get_width()) // 2, opt_y + 80))
    pygame.display.flip()


def draw_instructions_screen():
    screen.fill(BG_COLOR)
    instructions = [
        'Instructions / Tutorial', '',
        'Use arrow keys to move.',
        'Collect carrots to score.',
        'Collect apples for speed boost!',
        'Avoid poison or you die!',
        'Avoid the pirate enemy.',
        'Every 3 carrots = the game gets harder.', '',
        'Controls:',
        'Arrow Keys - Move   P - Pause I - Help', '',
        'Press any key to return.'
    ]
    y = 60
    for line in instructions:
        surf = font.render(line, True, (225, 105, 180))
        screen.blit(surf, ((WIDTH - surf.get_width()) // 2, y))
        y += 30
    pygame.display.flip()


def spawn_obstacles(n, reserved):
    obs = []
    attempts = 0
    margin = PLAYER_SIZE
    while len(obs) < n and attempts < 1000:
        x = random.randint(margin, WIDTH - OBSTACLE_SIZE - margin)
        y = random.randint(margin, HEIGHT - OBSTACLE_SIZE - margin)
        r = pygame.Rect(x, y, OBSTACLE_SIZE, OBSTACLE_SIZE)
        if any(r.colliderect(rr) for rr in reserved + obs):
            attempts += 1
            continue
        obs.append(r)
        attempts += 1
    return obs


def spawn_item(obstacles):
    attempts = 0
    while attempts < 1000:
        x = random.randint(0, WIDTH - ITEM_SIZE)
        y = random.randint(0, HEIGHT - ITEM_SIZE)
        r = pygame.Rect(x, y, ITEM_SIZE, ITEM_SIZE)
        if not any(r.colliderect(o) for o in obstacles):
            return [x, y]
        attempts += 1
    return None


def draw_game(player, enemy, carrot, apple, poison, score, level, high, obstacles):
    screen.fill(BG_COLOR)
    if carrot:
        if carrot_sprite:
            screen.blit(carrot_sprite, carrot)
        else:
            pygame.draw.ellipse(screen, CARROT_COLOR, (*carrot, ITEM_SIZE, ITEM_SIZE))
    if apple:
        if apple_sprite:
            screen.blit(apple_sprite, apple)
        else:
            pygame.draw.ellipse(screen, APPLE_COLOR, (*apple, ITEM_SIZE, ITEM_SIZE))
    if poison:
        if poison_sprite:
            screen.blit(poison_sprite, poison)
        else:
            pygame.draw.ellipse(screen, POISON_COLOR, (*poison, ITEM_SIZE, ITEM_SIZE))
    for o in obstacles:
        if bush_sprite:
            screen.blit(bush_sprite, (o.x, o.y))
        else:
            pygame.draw.rect(screen, BUSH_COLOR, o, border_radius=8)
    if level < 2:
        spr = default_player
    else:
        idx = ((level // 2) - 1) % len(chunkier_sprites)
        spr = chunkier_sprites[idx] or default_player
    if spr:
        screen.blit(spr, player)
    else:
        pygame.draw.rect(screen, APPLE_COLOR, (*player, PLAYER_SIZE, PLAYER_SIZE), border_radius=8)
    if enemy_sprite:
        screen.blit(enemy_sprite, enemy)
    else:
        pygame.draw.rect(screen, HUD_COLOR, (*enemy, ENEMY_SIZE, ENEMY_SIZE), border_radius=8)
    screen.blit(font.render(f'Score:{score}', True, HUD_COLOR), (15, 15))
    screen.blit(font.render(f'Lvl:{level}', True, HUD_COLOR), (15, 45))
    screen.blit(font.render(f'Best:{high}', True, HUD_COLOR), (15, 75))
    pygame.display.flip()


def run_game(ob_count, enemy_speed):
    player = [WIDTH // 4, HEIGHT // 2]
    enemy = [3 * WIDTH // 4, HEIGHT // 2]
    speed = NORMAL_SPEED
    boost_end = 0
    carrot = poison = apple = None
    history = []
    paused = False
    score = 0
    level = 1
    next_lvl = 3
    reserved = [
        pygame.Rect(*player, PLAYER_SIZE, PLAYER_SIZE),
        pygame.Rect(*enemy, ENEMY_SIZE, ENEMY_SIZE)
    ]
    obstacles = spawn_obstacles(ob_count, reserved)
    carrot = spawn_item(obstacles)
    high = load_high_score()
    while True:
        clock.tick(FPS)
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_p:
                    paused = not paused
                if e.key == pygame.K_i:
                    draw_instructions_screen()
                    waiting = True
                    while waiting:
                        for ev in pygame.event.get():
                            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                                waiting = False
        if paused:
            screen.fill(BG_COLOR)
            draw_text_centered('PAUSED', -20, color=(225, 105, 180))
            draw_text_centered('Press P to resume, I for help', 20, color=(225, 105, 180))
            pygame.display.flip()
            continue
        if boost_end and now > boost_end:
            speed = NORMAL_SPEED
            boost_end = 0
        keys = pygame.key.get_pressed()
        newp = player.copy()
        if keys[pygame.K_LEFT]:
            newp[0] -= speed
        if keys[pygame.K_RIGHT]:
            newp[0] += speed
        if keys[pygame.K_UP]:
            newp[1] -= speed
        if keys[pygame.K_DOWN]:
            newp[1] += speed
        prect = pygame.Rect(*newp, PLAYER_SIZE, PLAYER_SIZE)
        if (0 <= newp[0] <= WIDTH - PLAYER_SIZE and
                0 <= newp[1] <= HEIGHT - PLAYER_SIZE and
                not any(prect.colliderect(o) for o in obstacles)):
            player = newp
        history.append(tuple(player))
        if len(history) > HISTORY_LIMIT:
            history.pop(0)
        if len(history) >= HISTORY_LIMIT:
            dx = (history[-1][0] - history[0][0]) // HISTORY_LIMIT
            dy = (history[-1][1] - history[0][1]) // HISTORY_LIMIT
            tx, ty = player[0] + dx, player[1] + dy
            nx = enemy[0] + (enemy_speed if enemy[0] < tx else -enemy_speed if enemy[0] > tx else 0)
            if pygame.Rect(nx, enemy[1], ENEMY_SIZE, ENEMY_SIZE).collidelist(obstacles) == -1:
                enemy[0] = nx
            ny = enemy[1] + (enemy_speed if enemy[1] < ty else -enemy_speed if enemy[1] > ty else 0)
            if pygame.Rect(enemy[0], ny, ENEMY_SIZE, ENEMY_SIZE).collidelist(obstacles) == -1:
                enemy[1] = ny
        if carrot and pygame.Rect(*player, PLAYER_SIZE, PLAYER_SIZE).colliderect(
                pygame.Rect(*carrot, ITEM_SIZE, ITEM_SIZE)):
            score += 1
            carrot = spawn_item(obstacles)
            if not apple and random.randint(1, 5) == 1:
                apple = spawn_item(obstacles)
            if not poison and random.randint(1, 5) == 1:
                poison = spawn_item(obstacles)
            if score >= next_lvl:
                level += 1
                next_lvl += 3
                if level % 2 == 0:
                    enemy_speed += 1
                reserved = [
                    pygame.Rect(*player, PLAYER_SIZE, PLAYER_SIZE),
                    pygame.Rect(*enemy, ENEMY_SIZE, ENEMY_SIZE)
                ]
                obstacles.extend(spawn_obstacles(2, reserved + obstacles))
        if apple and pygame.Rect(*player, PLAYER_SIZE, PLAYER_SIZE).colliderect(
                pygame.Rect(*apple, ITEM_SIZE, ITEM_SIZE)):
            speed = BOOST_SPEED
            boost_end = now + BOOST_DURATION
            apple = None
        if poison and pygame.Rect(*player, PLAYER_SIZE, PLAYER_SIZE).colliderect(
                pygame.Rect(*poison, ITEM_SIZE, ITEM_SIZE)):
            animate_fly_to_heaven(player)
            return
        if pygame.Rect(*player, PLAYER_SIZE, PLAYER_SIZE).colliderect(
                pygame.Rect(*enemy, ENEMY_SIZE, ENEMY_SIZE)):
            animate_fly_to_heaven(player)
            if score > high:
                save_high_score(score)
            return
        draw_game(player, enemy, carrot, apple, poison, score, level, high, obstacles)


def game_over():
    screen.fill(BG_COLOR)
    draw_text_centered('Game Over! Press R to restart', -20, color=(225, 105, 180))
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                return


if __name__ == '__main__':
    selected = "Easy"
    draw_start_screen(selected)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1:
                    selected = "Easy"
                elif e.key == pygame.K_2:
                    selected = "Medium"
                elif e.key == pygame.K_3:
                    selected = "Hard"
                elif e.key == pygame.K_i:
                    draw_instructions_screen()
                    waiting = True
                    while waiting:
                        for ev in pygame.event.get():
                            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                                waiting = False
                elif e.key == pygame.K_RETURN:
                    break
        else:
            draw_start_screen(selected)
            continue
        break
    while True:
        obs_count, e_speed = get_difficulty_settings(selected)
        run_game(obs_count, e_speed)
        game_over()
