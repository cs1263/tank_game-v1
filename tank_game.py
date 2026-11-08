import sys
import math
import random
import pygame

WINDOW_SIZE = (900, 700)
BG_COLOR = (25, 25, 30)
FPS = 60

# gameplay settings
PLAYER_SPEED = 220  # px/s
BULLET_SPEED = 600
BULLET_LIFETIME = 1.5
ENEMY_SPEED = 100
SPAWN_INTERVAL = 2.0

class Bullet:
    def __init__(self, pos, vel):
        self.pos = list(pos)
        self.vel = list(vel)
        self.life = BULLET_LIFETIME

    def update(self, dt):
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.life -= dt

    def draw(self, surf):
        pygame.draw.circle(surf, (255, 220, 80), (int(self.pos[0]), int(self.pos[1])), 4)

    def is_alive(self):
        return self.life > 0 and 0 <= self.pos[0] <= WINDOW_SIZE[0] and 0 <= self.pos[1] <= WINDOW_SIZE[1]

class Tank:
    def __init__(self, x, y, color=(80,200,120)):
        self.x = x
        self.y = y
        self.angle = 0.0
        self.color = color
        self.size = (40, 28)  # body width, body height
        self.turret_length = 24
        self.hp = 3

    def draw(self, surf):
        body_rect = pygame.Rect(0,0, self.size[0], self.size[1])
        body_rect.center = (self.x, self.y)
        # rotate body
        body_surf = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(body_surf, self.color, body_surf.get_rect(), border_radius=6)
        rotated = pygame.transform.rotate(body_surf, -math.degrees(self.angle))
        rrect = rotated.get_rect(center=(self.x, self.y))
        surf.blit(rotated, rrect.topleft)
        # turret
        end_x = self.x + math.cos(self.angle) * self.turret_length
        end_y = self.y + math.sin(self.angle) * self.turret_length
        pygame.draw.line(surf, (40,40,40), (self.x, self.y), (end_x, end_y), 6)
        pygame.draw.circle(surf, (30,30,30), (int(self.x), int(self.y)), 6)

    def rect(self):
        return pygame.Rect(self.x - self.size[0]/2, self.y - self.size[1]/2, self.size[0], self.size[1])

def spawn_enemy():
    side = random.choice(['left','right','top','bottom'])
    if side == 'left':
        return Tank(-30, random.uniform(0, WINDOW_SIZE[1]), color=(200,80,80))
    if side == 'right':
        return Tank(WINDOW_SIZE[0]+30, random.uniform(0, WINDOW_SIZE[1]), color=(200,80,80))
    if side == 'top':
        return Tank(random.uniform(0, WINDOW_SIZE[0]), -30, color=(200,80,80))
    return Tank(random.uniform(0, WINDOW_SIZE[0]), WINDOW_SIZE[1]+30, color=(200,80,80))

def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Tanker Shooting - Simple Demo")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 26)

    player = Tank(WINDOW_SIZE[0]/2, WINDOW_SIZE[1]/2, color=(80,160,220))
    bullets = []
    enemies = []
    spawn_timer = 1.0
    score = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # shoot bullet from turret tip
                mx, my = pygame.mouse.get_pos()
                angle = math.atan2(my - player.y, mx - player.x)
                bx = player.x + math.cos(angle) * player.turret_length
                by = player.y + math.sin(angle) * player.turret_length
                vx = math.cos(angle) * BULLET_SPEED
                vy = math.sin(angle) * BULLET_SPEED
                bullets.append(Bullet((bx, by), (vx, vy)))

        # input -> movement
        keys = pygame.key.get_pressed()
        move_x = (keys[pygame.K_d] - keys[pygame.K_a])
        move_y = (keys[pygame.K_s] - keys[pygame.K_w])
        if move_x != 0 or move_y != 0:
            norm = math.hypot(move_x, move_y) or 1
            player.x += (move_x / norm) * PLAYER_SPEED * dt
            player.y += (move_y / norm) * PLAYER_SPEED * dt
        # clamp player inside window
        player.x = max(20, min(WINDOW_SIZE[0]-20, player.x))
        player.y = max(20, min(WINDOW_SIZE[1]-20, player.y))

        # update turret direction to mouse
        mx, my = pygame.mouse.get_pos()
        player.angle = math.atan2(my - player.y, mx - player.x)

        # spawn enemies
        spawn_timer -= dt
        if spawn_timer <= 0:
            enemies.append(spawn_enemy())
            spawn_timer = max(0.6, SPAWN_INTERVAL - score*0.03)

        # update bullets
        for b in bullets:
            b.update(dt)
        bullets = [b for b in bullets if b.is_alive()]

        # update enemies: simple chase
        for e in enemies:
            dx = player.x - e.x
            dy = player.y - e.y
            dist = math.hypot(dx, dy) or 1
            e.angle = math.atan2(dy, dx)
            e.x += (dx / dist) * ENEMY_SPEED * dt
            e.y += (dy / dist) * ENEMY_SPEED * dt

        # collisions: bullet vs enemy
        alive_enemies = []
        for e in enemies:
            hit = False
            for b in bullets:
                if math.hypot(b.pos[0]-e.x, b.pos[1]-e.y) < 18:
                    hit = True
                    b.life = 0
                    score += 1
                    break
            if not hit:
                alive_enemies.append(e)
        enemies = alive_enemies
        bullets = [b for b in bullets if b.is_alive()]

        # enemy vs player collision
        for e in enemies:
            if math.hypot(e.x - player.x, e.y - player.y) < 28:
                player.hp -= 1
                # push enemy away
                ang = math.atan2(e.y - player.y, e.x - player.x)
                e.x += math.cos(ang) * 40
                e.y += math.sin(ang) * 40

        # remove dead player
        if player.hp <= 0:
            running = False

        # render
        screen.fill(BG_COLOR)
        # draw bullets
        for b in bullets:
            b.draw(screen)
        # draw enemies
        for e in enemies:
            e.draw(screen)
        # draw player
        player.draw(screen)

        # UI
        ui = font.render(f"HP: {player.hp}   Score: {score}   Enemies: {len(enemies)}", True, (220,220,220))
        screen.blit(ui, (10,10))
        pygame.display.flip()

    # game over screen
    screen.fill((12,12,12))
    go = font.render(f"Game Over  Score: {score}  (ESC to exit)", True, (240,240,240))
    screen.blit(go, (WINDOW_SIZE[0]//2 - go.get_width()//2, WINDOW_SIZE[1]//2 - 10))
    pygame.display.flip()
    # wait until quit
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()
