import os, sys, math, random, pygame

# --------- Config ----------
WIN_W, WIN_H = 960, 540
TITLE = "Space Adventure - Reach the Sun"
FPS = 60

# Colors
WHITE = (240, 244, 255)
HUD = (220, 235, 255)
RED = (255, 90, 90)
YELLOW = (255, 204, 51)
CYAN = (140, 220, 255)
DARK = (11, 15, 26)

PLAYER_SPEED = 6
BASE_MON_SPEED = 1.8
CHASE_SPEED = 3.0
CHASE_RANGE = 220
SPAWN_MON_MS = 3000
SPAWN_COIN_MS = 1400
RAMP_MS = 12000
MAX_LIVES = 3

ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

def resource_path(rel):
    # Works in PyInstaller bundles
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(rel)

def load_image(name, scale=None):
    p = os.path.join(ASSET_DIR, name)
    if not os.path.exists(p):
        return None
    img = pygame.image.load(p).convert_alpha()
    if scale:
        img = pygame.transform.smoothscale(img, scale)
    return img

def get_window_size(screen):
    return screen.get_width(), screen.get_height()

class Parallax:
    def __init__(self, screen):
        self.screen = screen
        self.layers = []
        img_names = ["bg_far.png", "bg_mid.png", "bg_near.png"]
        speeds = [0.2, 0.5, 1.0]
        for name, spd in zip(img_names, speeds):
            img = load_image(name)
            if img:
                self.layers.append({"img": img, "x": 0.0, "speed": spd})
        self.procedural = len(self.layers) == 0
        if self.procedural:
            self.stars_far = [(random.randrange(WIN_W), random.randrange(WIN_H)) for _ in range(140)]
            self.stars_mid = [(random.randrange(WIN_W), random.randrange(WIN_H)) for _ in range(90)]
            self.stars_near = [(random.randrange(WIN_W), random.randrange(WIN_H)) for _ in range(60)]
            self.off_far = 0.0
            self.off_mid = 0.0
            self.off_near = 0.0

    def update(self, dx):
        if self.procedural:
            self.off_far = (self.off_far + dx * 0.2) % WIN_W
            self.off_mid = (self.off_mid + dx * 0.5) % WIN_W
            self.off_near = (self.off_near + dx * 1.0) % WIN_W
            return
        for L in self.layers:
            L["x"] = (L["x"] + dx * L["speed"]) % L["img"].get_width()

    def draw(self):
        if self.procedural:
            self.screen.fill(DARK)
            for x, y in self.stars_far:
                pygame.draw.circle(self.screen, (32, 48, 78), (int((x - self.off_far) % WIN_W), y), 1)
            for x, y in self.stars_mid:
                pygame.draw.circle(self.screen, (45, 68, 108), (int((x - self.off_mid) % WIN_W), y), 2)
            for x, y in self.stars_near:
                pygame.draw.circle(self.screen, (70, 110, 170), (int((x - self.off_near) % WIN_W), y), 2)
            return
        # draw tiled layers left-to-right for each
        for L in self.layers:
            img = L["img"]; x = -L["x"]; w = img.get_width()
            self.screen.blit(img, (int(x), 0))
            self.screen.blit(img, (int(x + w), 0))

class Shuttle:
    def __init__(self):
        self.img = load_image("shuttle.png", (60, 72))
        self.rect = pygame.Rect(60, WIN_H//2 - 30, 40, 60)
        self.color = CYAN
        self.speed = PLAYER_SPEED
        self.invuln_ms = 0

    def update(self, keys, dt):
        dx = dy = 0
        if keys[pygame.K_LEFT]:  dx -= self.speed
        if keys[pygame.K_RIGHT]: dx += self.speed
        if keys[pygame.K_UP]:    dy -= self.speed
        if keys[pygame.K_DOWN]:  dy += self.speed
        self.rect.x += dx; self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIN_W, WIN_H))
        if self.invuln_ms > 0:
            self.invuln_ms -= dt

    def draw(self, screen, blink=False):
        if self.img:
            img = self.img
            if blink and (pygame.time.get_ticks() // 120) % 2 == 0:
                img = img.copy(); img.fill((255,255,255,160), None, pygame.BLEND_RGBA_MULT)
            screen.blit(img, img.get_rect(center=self.rect.center))
        else:
            col = WHITE if blink and (pygame.time.get_ticks() // 120) % 2 == 0 else self.color
            pygame.draw.polygon(screen, col, [
                (self.rect.centerx, self.rect.top),
                (self.rect.left, self.rect.bottom),
                (self.rect.right, self.rect.bottom)
            ])

class Monster:
    def __init__(self, level):
        r = random.randint(16, 24)
        edge = random.choice(["left","right","top","bottom"])
        if edge == "left":
            x, y = -30, random.randint(20, WIN_H-20)
        elif edge == "right":
            x, y = WIN_W+30, random.randint(20, WIN_H-20)
        elif edge == "top":
            x, y = random.randint(20, WIN_W-20), -30
        else:
            x, y = random.randint(20, WIN_W-20), WIN_H+30
        self.rect = pygame.Rect(x-r, y-r, r*2, r*2)
        self.r = r
        self.mode = "wander"
        spd = BASE_MON_SPEED + 0.2*(level-1)
        self.vx = (random.random()*2-1) * spd
        self.vy = (random.random()*2-1) * spd
        self.color = RED

    def update(self, px, py, level):
        mx, my = self.rect.center
        dist = math.hypot(px - mx, py - my)
        if dist < CHASE_RANGE:
            self.mode = "chase"
        if self.mode == "chase":
            ux, uy = ((px - mx)/dist, (py - my)/dist) if dist else (0,0)
            spd = CHASE_SPEED + 0.25*(level-1)
            self.vx, self.vy = ux*spd, uy*spd
        else:
            self.vx += random.uniform(-0.05, 0.05)
            self.vy += random.uniform(-0.05, 0.05)
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)
        pygame.draw.ellipse(screen, (255,160,160), self.rect, 2)

    def offscreen_far(self):
        x, y = self.rect.center
        return x < -100 or x > WIN_W+100 or y < -100 or y > WIN_H+100

class Coin:
    def __init__(self):
        self.img = load_image("coin.png", (28, 28))
        x = random.randint(140, WIN_W-140)
        y = random.randint(60, WIN_H-60)
        self.rect = pygame.Rect(x-14, y-14, 28, 28)
        self.t = random.random()*math.tau

    def update(self):
        self.t += 0.15
    def draw(self, screen):
        if self.img:
            img = pygame.transform.rotozoom(self.img, (math.sin(self.t)*10), 1.0)
            screen.blit(img, img.get_rect(center=self.rect.center))
        else:
            c = (255, 210, 60)
            pygame.draw.circle(screen, c, self.rect.center, 12)
            pygame.draw.circle(screen, (255, 240, 160), self.rect.center, 12, 2)

def draw_sun(screen, x, y):
    img = load_image("sun.png", (120,120))
    if img:
        screen.blit(img, img.get_rect(center=(x,y)))
    else:
        pygame.draw.circle(screen, YELLOW, (x,y), 60)
        pygame.draw.circle(screen, (255,180,0), (x,y), 60, 6)

def text(surface, s, x, y, size=20, color=HUD, center=False):
    font = pygame.font.SysFont("Arial", size, bold=True)
    surf = font.render(s, True, color)
    rect = surf.get_rect()
    rect.center = (x,y) if center else (x+rect.width//2, y+rect.height//2)
    if center:
        surface.blit(surf, rect)
    else:
        surface.blit(surf, (x, y))

def start_screen(screen):
    clock = pygame.time.Clock()
    name, age = "", ""
    active = "name"
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_TAB:
                    active = "age" if active=="name" else "name"
                elif e.key == pygame.K_RETURN:
                    if not name: name="Explorer"
                    if not age.isdigit(): age="8"
                    return name, int(age)
                elif e.key == pygame.K_BACKSPACE:
                    if active=="name" and name: name=name[:-1]
                    elif active=="age" and age: age=age[:-1]
                else:
                    ch = e.unicode
                    if active=="name" and len(name) < 16 and ch.isprintable():
                        name += ch
                    if active=="age" and ch.isdigit() and len(age) < 2:
                        age += ch
        # draw UI
        screen.fill((16,20,34))
        w, h = get_window_size(screen)
        text(screen, "SPACE ADVENTURE", w//2, int(h*0.22), 48, WHITE, True)
        text(screen, "Pilot Name:", w//2-180, int(h*0.4), 26)
        # name field
        name_rect = pygame.Rect(w//2-20, int(h*0.38), 260, 36)
        pygame.draw.rect(screen, (46,64,110), name_rect, border_radius=8)
        text(screen, name or "Explorer", name_rect.centerx, name_rect.centery-12, 24, WHITE, True)

        text(screen, "Age:", w//2-180, int(h*0.49), 26)
        age_rect = pygame.Rect(w//2-20, int(h*0.47), 260, 36)
        pygame.draw.rect(screen, (46,64,110), age_rect, border_radius=8)
        text(screen, age or "8", age_rect.centerx, age_rect.centery-12, 24, WHITE, True)

        hint = "Tab to switch fields • Enter to Start • Arrow keys to move"
        text(screen, hint, w//2, int(h*0.62), 20, (200,220,255), True)

        # focus ring
        ring = name_rect if active=="name" else age_rect
        pygame.draw.rect(screen, (95,140,220), ring, 2, border_radius=8)

        pygame.display.flip()
        clock.tick(60)

def main():
    global SPAWN_MON_MS, SPAWN_COIN_MS
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE)
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    name, age = start_screen(screen)

    parallax = Parallax(screen)
    player = Shuttle()
    monsters, coins = [], []
    lives, score, level, distance = MAX_LIVES, 0, 1, 0
    sun_x = WIN_W + 2800
    sun_y = WIN_H//2

    last_mon = last_coin = last_ramp = 0
    running, win = True, False
    start_ticks = pygame.time.get_ticks()

    while running:
        dt = clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            elif e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)

        keys = pygame.key.get_pressed()
        player.update(keys, dt)

        # smooth rightward camera scroll (speed up when holding Right)
        scroll_dx = 1.0 + (1.0 if keys[pygame.K_RIGHT] else 0.0)
        distance += scroll_dx
        sun_screen_x = int(sun_x - distance)
        parallax.update(scroll_dx)

        # Spawns and ramp
        t = pygame.time.get_ticks()
        if t - last_mon >= SPAWN_MON_MS:
            monsters.append(Monster(level)); last_mon = t
        if t - last_coin >= SPAWN_COIN_MS:
            coins.append(Coin()); last_coin = t
        if t - last_ramp >= RAMP_MS:
            level += 1
            SPAWN_MON_MS = max(1200, SPAWN_MON_MS - 150)
            SPAWN_COIN_MS = max(600, SPAWN_COIN_MS - 60)
            last_ramp = t

        # Updates
        px, py = player.rect.center
        for m in monsters[:]:
            m.update(px, py, level)
            if m.offscreen_far(): monsters.remove(m)
        for c in coins: c.update()

        # Collisions
        if player.invuln_ms <= 0:
            for m in monsters:
                if player.rect.colliderect(m.rect):
                    lives -= 1
                    player.invuln_ms = 1200
                    if lives <= 0: running = False
                    break
        for c in coins[:]:
            if player.rect.colliderect(c.rect):
                score += 10
                coins.remove(c)

        # Win
        if sun_screen_x <= player.rect.centerx + 40:
            win = True; running = False

        # Draw order: parallax -> mid planets -> sun -> coins/monsters -> player -> HUD
        parallax.draw()

        # stylized mid-ground planets (only if no mid layer art covers them)
        w, h = get_window_size(screen)
        pygame.draw.circle(screen, (65,85,140), (int(w*0.21), int(h*0.26)), 80, 0)
        pygame.draw.circle(screen, (88,50,130), (int(w*0.75), int(h*0.22)), 60, 0)

        draw_sun(screen, max(100, sun_screen_x), sun_y)

        for c in coins: c.draw(screen)
        for m in monsters: m.draw(screen)
        player.draw(screen, blink=player.invuln_ms>0)

        # HUD
        text(screen, f"Pilot: {name}  Age: {age}", 12, 8, 18)
        text(screen, f"Lives: {lives}", 12, 30, 18)
        text(screen, f"Score: {score}", 12, 52, 18)
        text(screen, f"Level: {level}", 12, 74, 18)
        text(screen, f"Distance: {int(distance)}", 12, 96, 18)

        pygame.display.flip()

    # End screen
    screen.fill(DARK)
    if win:
        text(screen, "You reached the Sun! Victory!", w//2, h//2-10, 36, WHITE, True); score += 100
    else:
        text(screen, "Game Over", w//2, h//2-10, 36, WHITE, True)
    text(screen, f"Final Score: {score}", w//2, h//2+40, 28, HUD, True)
    text(screen, "Press Enter to play again, Esc to quit", w//2, h//2+90, 22, (200,220,255), True)
    pygame.display.flip()

    again = False
    wait = True
    while wait:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN: again = True; wait = False
                if e.key == pygame.K_ESCAPE: wait = False
        pygame.time.delay(16)
    if again:
        main()

if __name__ == "__main__":
    main()
