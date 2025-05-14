import pygame
import random
import sys
import os

pygame.init()

WIDTH, HEIGHT = 800, 600
TITLE = "Animal Escape"
FPS = 60
PLAYER_SIZE = ENEMY_SIZE = 60
ITEM_SIZE = 20
OBSTACLE_SIZE = 60
HISTORY_LIMIT = 30
HIGH_SCORE_FILE = "high_score.txt"

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

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
chunkier_sprites = [load_image(f"chunkier-stefanek-pic-{i}.png", (PLAYER_SIZE, PLAYER_SIZE)) for i in range(5)]
enemy_sprite = load_image("pirat.png", (ENEMY_SIZE, ENEMY_SIZE))
carrot_sprite = load_image("carrot.png", (ITEM_SIZE, ITEM_SIZE))
bush_sprite = load_image("bush.png", (OBSTACLE_SIZE, OBSTACLE_SIZE))

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
    speeds = {"Easy": (3,1), "Medium": (6,2), "Hard": (10,3)}
    return speeds.get(level, (3,1))

def draw_text_centered(text, y_offset=0, color=BLACK):
    surf = font.render(text, True, color)
    x = (WIDTH - surf.get_width()) // 2
    y = (HEIGHT - surf.get_height()) // 2 + y_offset
    screen.blit(surf, (x, y))

def draw_start_screen(selected):
    screen.fill(WHITE)
    draw_text_centered('Select Difficulty: [1]Easy [2]Medium [3]Hard', -50)
    draw_text_centered(f'Current: {selected}', 10, RED)
    draw_text_centered('Press I for Instructions', 80)
    pygame.display.flip()

def draw_instructions_screen():
    screen.fill(WHITE)
    instructions = [
        'Instructions / Tutorial', '',
        'Use arrow keys to move.',
        'Collect carrots to score.',
        'Avoid the pirate enemy.',
        'Every 3 carrots = harder.', '',
        'Controls:',
        'Arrow Keys-Move  P-Pause  R-Restart  I-Help', '',
        'Press any key to return.'
    ]
    y=50
    for line in instructions:
        surf = font.render(line, True, BLACK)
        screen.blit(surf, ((WIDTH-surf.get_width())//2, y)); y+=35
    pygame.display.flip()

def spawn_obstacles(n, reserved_rects):
    obs=[]
    attempts=0
    while len(obs)<n and attempts<1000:
        x=random.randint(0, WIDTH-OBSTACLE_SIZE)
        y=random.randint(0, HEIGHT-OBSTACLE_SIZE)
        r=pygame.Rect(x,y,OBSTACLE_SIZE,OBSTACLE_SIZE)
        if any(r.colliderect(rr) for rr in reserved_rects+obs):
            attempts+=1; continue
        obs.append(r); attempts+=1
    return obs

def spawn_carrot(obstacles):
    attempts=0
    while attempts<1000:
        x=random.randint(0, WIDTH-ITEM_SIZE)
        y=random.randint(0, HEIGHT-ITEM_SIZE)
        r=pygame.Rect(x,y,ITEM_SIZE,ITEM_SIZE)
        if not any(r.colliderect(o) for o in obstacles):
            return [x,y]
        attempts+=1
    return [0,0]

def draw_game(player, enemy, carrot, score, level, high, obstacles):
    screen.fill(WHITE)

    if carrot_sprite: screen.blit(carrot_sprite, carrot)
    else: pygame.draw.rect(screen, (255,165,0), (*carrot,ITEM_SIZE,ITEM_SIZE))

    for o in obstacles:
        if bush_sprite: screen.blit(bush_sprite,(o.x,o.y))
        else: pygame.draw.rect(screen,(100,100,100),o)

    if level>=2:
        idx=((level//2)-1)%len(chunkier_sprites)
        spr=chunkier_sprites[idx] or default_player
    else: spr=default_player
    if spr: screen.blit(spr, player)
    else: pygame.draw.rect(screen,(0,255,0),(*player,PLAYER_SIZE,PLAYER_SIZE))
    # Draw enemy
    if enemy_sprite: screen.blit(enemy_sprite, enemy)
    else: pygame.draw.rect(screen,RED,(*enemy,ENEMY_SIZE,ENEMY_SIZE))

    screen.blit(font.render(f'Score:{score}',True,BLACK),(10,10))
    screen.blit(font.render(f'Level:{level}',True,BLACK),(10,40))
    screen.blit(font.render(f'Best:{high}',True,BLACK),(10,70))
    pygame.display.flip()

def run_game(ob_count, enemy_speed):
    player=[WIDTH//4,HEIGHT//2]
    enemy=[3*WIDTH//4,HEIGHT//2]
    speed=5; history=[]; paused=False
    score=0;level=1;next_lvl=3

    reserved=[pygame.Rect(*player,PLAYER_SIZE,PLAYER_SIZE),pygame.Rect(*enemy,ENEMY_SIZE,ENEMY_SIZE)]
    obstacles=spawn_obstacles(ob_count,reserved)
    carrot=spawn_carrot(obstacles)
    high=load_high_score()
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_p: paused=not paused
                elif e.key==pygame.K_i:
                    draw_instructions_screen();
                    wait=True
                    while wait:
                        for ev in pygame.event.get():
                            if ev.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN): wait=False
        if paused:
            screen.fill(WHITE)
            draw_text_centered('PAUSED',-20)
            draw_text_centered('Press P to Resume, I for Help',20)
            pygame.display.flip()
            continue

        keys=pygame.key.get_pressed(); newp=player.copy()
        if keys[pygame.K_LEFT]: newp[0]-=speed
        if keys[pygame.K_RIGHT]: newp[0]+=speed
        if keys[pygame.K_UP]: newp[1]-=speed
        if keys[pygame.K_DOWN]: newp[1]+=speed
        prect=pygame.Rect(*newp,PLAYER_SIZE,PLAYER_SIZE)
        if 0<=newp[0]<=WIDTH-PLAYER_SIZE and 0<=newp[1]<=HEIGHT-PLAYER_SIZE and not any(prect.colliderect(o) for o in obstacles):
            player=newp

        history.append(tuple(player))
        if len(history)>HISTORY_LIMIT: history.pop(0)
        if len(history)>=2:
            dx=(history[-1][0]-history[0][0])//HISTORY_LIMIT
            dy=(history[-1][1]-history[0][1])//HISTORY_LIMIT
            tx,ty=player[0]+dx,player[1]+dy

            nx=enemy[0]+(enemy_speed if enemy[0]<tx else -enemy_speed if enemy[0]>tx else 0)
            if not pygame.Rect(nx,enemy[1],ENEMY_SIZE,ENEMY_SIZE).collidelist(obstacles)!=-1: enemy[0]=nx

            ny=enemy[1]+(enemy_speed if enemy[1]<ty else -enemy_speed if enemy[1]>ty else 0)
            if not pygame.Rect(enemy[0],ny,ENEMY_SIZE,ENEMY_SIZE).collidelist(obstacles)!=-1: enemy[1]=ny

        if pygame.Rect(*player,PLAYER_SIZE,PLAYER_SIZE).colliderect(pygame.Rect(*carrot,ITEM_SIZE,ITEM_SIZE)):
            score+=1; carrot=spawn_carrot(obstacles)
            if score>=next_lvl:
                level+=1; enemy_speed+=1; obstacles+=spawn_obstacles(2,reserved); next_lvl+=3

        if pygame.Rect(*player,PLAYER_SIZE,PLAYER_SIZE).colliderect(pygame.Rect(*enemy,ENEMY_SIZE,ENEMY_SIZE)):
            if score>high: save_high_score(score)
            return
        draw_game(player,enemy,carrot,score,level,high,obstacles)


def game_over():
    screen.fill(WHITE)
    draw_text_centered('Game Over! Press R to restart')
    pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN and e.key==pygame.K_r: return


if __name__=='__main__':
    sel="Easy"
    draw_start_screen(sel)
    while True:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit();sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_1: sel="Easy"
                elif e.key==pygame.K_2: sel="Medium"
                elif e.key==pygame.K_3: sel="Hard"
                elif e.key==pygame.K_i:
                    draw_instructions_screen(); wait=True
                    while wait:
                        for ev in pygame.event.get():
                            if ev.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN): wait=False
                elif e.key==pygame.K_RETURN: break
        else:
            draw_start_screen(sel); continue
        break
    while True:
        oc,es=get_difficulty_settings(sel)
        run_game(oc,es)
        game_over()
