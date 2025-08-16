import pygame
import random
import math
import sys
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# For Pydroid 3 specific settings
try:
    os.environ['SDL_TEXTINPUT'] = '0'
    os.environ['SDL_IME_SHOW_UI'] = '0'
except:
    pass

# Screen setup
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = 12
BALL_SIZE = 90
SPIKE_WIDTH = 120
SPIKE_HEIGHT = 180
BALL_SPEED = 6

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vel_y = 0
        self.gravity_up = False
        self.size = BALL_SIZE
        self.can_switch_gravity = False

    def update(self):
        GRAVITY_FORCE = 1.6
        if self.gravity_up:
            self.vel_y -= GRAVITY_FORCE
        else:
            self.vel_y += GRAVITY_FORCE

        self.y += self.vel_y

        screen_height = pygame.display.get_surface().get_height()
        is_grounded = False

        if self.y < self.size:
            self.y = self.size
            self.vel_y = 0
            is_grounded = True
        elif self.y > screen_height - self.size:
            self.y = screen_height - self.size
            self.vel_y = 0
            is_grounded = True

        self.can_switch_gravity = is_grounded

    def switch_gravity(self):
        if self.can_switch_gravity:
            self.gravity_up = not self.gravity_up
            self.vel_y = 0  # reset velocity for consistent fall time
            self.can_switch_gravity = False

    def draw(self, screen):
        if self.can_switch_gravity:
            pygame.draw.circle(screen, (100, 200, 255),
                               (int(self.x), int(self.y)),
                               self.size + 10, 5)
        pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size, 5)


class Spike:
    def __init__(self, x, spike_type):
        self.x = x
        self.spike_type = spike_type
        self.width = SPIKE_WIDTH
        self.height = SPIKE_HEIGHT
        screen_height = pygame.display.get_surface().get_height()

        if spike_type == 'up':
            self.y = screen_height - self.height
        else:
            self.y = 0

    def update(self, speed):
        self.x -= speed

    def draw(self, screen):
        if self.spike_type == 'up':
            points = [
                (self.x, self.y + self.height),
                (self.x + self.width // 2, self.y),
                (self.x + self.width, self.y + self.height)
            ]
        else:
            points = [
                (self.x, self.y),
                (self.x + self.width // 2, self.y + self.height),
                (self.x + self.width, self.y)
            ]
        pygame.draw.polygon(screen, RED, points)
        pygame.draw.polygon(screen, BLACK, points, 5)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Game:
    def __init__(self):
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        try:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        except:
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Gravity Shift Game")
        try:
            pygame.key.stop_text_input()
        except:
            pass

        self.clock = pygame.time.Clock()
        font_size = max(48, int(self.screen_width * 0.08))
        large_font_size = max(72, int(self.screen_width * 0.12))
        self.font = pygame.font.Font(None, font_size)
        self.large_font = pygame.font.Font(None, large_font_size)

        # Load and setup background music
        self.music_loaded = False
        self.load_background_music()

        self.reset_game()
        self.state = "menu"

    def load_background_music(self):
        """Load the Undyne background music"""
        music_file = "music.mp3"
        try:
            if os.path.exists(music_file):
                pygame.mixer.music.load(music_file)
                self.music_loaded = True
                print("Background music loaded successfully!")
            else:
                print(f"Music file not found: {music_file}")
        except pygame.error as e:
            print(f"Could not load music: {e}")
            self.music_loaded = False

    def start_background_music(self):
        """Start playing background music on loop"""
        if self.music_loaded:
            try:
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                pygame.mixer.music.set_volume(0.7)  # Set volume to 70%
            except pygame.error as e:
                print(f"Could not play music: {e}")

    def stop_background_music(self):
        """Stop the background music"""
        if self.music_loaded:
            pygame.mixer.music.stop()

    def reset_game(self):
        self.ball = Ball(150, self.screen_height // 2)
        self.spikes = []
        self.score = 0
        self.speed = BALL_SPEED
        self.spike_timer = 0
        self.difficulty_timer = 0

    def generate_spike_pattern(self):
        min_gap = 300 + random.randint(0, 150)
        spike_config = random.choice([
            "single_up", "single_down", "gap_middle", "safe_passage"
        ])
        last_x = max([s.x for s in self.spikes], default=0)
        next_x = max(self.screen_width + 100, last_x + min_gap)

        if spike_config == "safe_passage":
            for i in range(2):
                self.spikes.append(Spike(next_x + i * 200,
                                         'up' if i % 2 == 0 else 'down'))
        else:
            t = 'up' if spike_config in ("single_up", "gap_middle") else 'down'
            self.spikes.append(Spike(next_x, t))

    def check_collisions(self):
        ball_rect = pygame.Rect(
            self.ball.x - self.ball.size,
            self.ball.y - self.ball.size,
            self.ball.size * 2,
            self.ball.size * 2
        )
        for spike in self.spikes:
            if ball_rect.colliderect(spike.get_rect()):
                center_x = spike.x + spike.width // 2
                tip_y = spike.y if spike.spike_type == 'up' else spike.y + spike.height
                dist = math.hypot(self.ball.x - center_x,
                                  self.ball.y - tip_y)
                if dist < self.ball.size + 15:
                    return True
        return False

    def update_difficulty(self):
        self.difficulty_timer += 1
        if self.difficulty_timer % (FPS * 15) == 0:
            self.speed *= 1.3  # Multiply speed by 1.3x every 15 seconds

    def draw_exit_button(self):
        size = 80; margin = 20
        r = pygame.Rect(self.screen_width - size - margin, margin, size, size)
        pygame.draw.rect(self.screen, RED, r)
        pygame.draw.rect(self.screen, WHITE, r, 3)
        cx, cy, off = r.centerx, r.centery, 20
        pygame.draw.line(self.screen, WHITE, (cx-off, cy-off), (cx+off, cy+off), 5)
        pygame.draw.line(self.screen, WHITE, (cx+off, cy-off), (cx-off, cy+off), 5)
        return r

    def draw_menu(self):
        self.screen.fill(BLACK)
        title = self.large_font.render("GRAVITY SHIFT", True, WHITE)
        tr = title.get_rect(center=(self.screen_width//2, self.screen_height//3))
        self.screen.blit(title, tr)

        bw = max(300, int(self.screen_width * 0.6))
        bh = max(100, int(self.screen_height * 0.12))
        btn = pygame.Rect(self.screen_width//2 - bw//2, self.screen_height//2, bw, bh)
        pygame.draw.rect(self.screen, GREEN, btn); pygame.draw.rect(self.screen, WHITE, btn, 2)
        play = self.font.render("PLAY", True, WHITE)
        self.screen.blit(play, play.get_rect(center=btn.center))

        inst = self.font.render("Tap screen to switch gravity when grounded!", True, WHITE)
        self.screen.blit(inst, inst.get_rect(center=(self.screen_width//2, self.screen_height//2+bh+60)))
        inst2 = self.font.render("Blue glow = can switch gravity", True, (100,200,255))
        self.screen.blit(inst2, inst2.get_rect(center=(self.screen_width//2,self.screen_height//2+bh+120)))

        # Show music status
        music_status = "♪ Music: ON" if self.music_loaded else "♪ Music: NOT LOADED"
        music_color = GREEN if self.music_loaded else RED
        music_text = pygame.font.Font(None, 36).render(music_status, True, music_color)
        self.screen.blit(music_text, (20, 20))

        exit_r = self.draw_exit_button()
        return btn, exit_r

    def draw_game(self):
        self.screen.fill(BLACK)
        pygame.draw.line(self.screen, WHITE, (0,self.screen_height-5),(self.screen_width,self.screen_height-5),5)
        pygame.draw.line(self.screen, WHITE, (0,5),(self.screen_width,5),5)
        for s in self.spikes: s.draw(self.screen)
        self.ball.draw(self.screen)

        sf = pygame.font.Font(None, max(36, int(self.screen_width*0.05)))
        self.screen.blit(sf.render(f"Score: {self.score}", True, WHITE),(20,self.screen_height-120))
        self.screen.blit(sf.render(f"Speed: {self.speed:.1f}", True, WHITE),(20,self.screen_height-80))
        status = sf.render("Can Switch Gravity" if self.ball.can_switch_gravity else "Cannot Switch", True,
                            GREEN if self.ball.can_switch_gravity else YELLOW)
        self.screen.blit(status,(20,20))

        return self.draw_exit_button()

    def draw_game_over(self):
        self.screen.fill(BLACK)
        go = self.large_font.render("GAME OVER", True, RED)
        self.screen.blit(go, go.get_rect(center=(self.screen_width//2, self.screen_height//3)))
        self.screen.blit(self.font.render(f"Final Score: {self.score}", True, WHITE),
                         self.font.render(f"Final Score: {self.score}", True, WHITE).get_rect(center=(self.screen_width//2, self.screen_height//2-80)))

        bw = max(300, int(self.screen_width * 0.6))
        bh = max(100, int(self.screen_height * 0.12))
        btn = pygame.Rect(self.screen_width//2 - bw//2, self.screen_height//2+20, bw, bh)
        pygame.draw.rect(self.screen, GREEN, btn); pygame.draw.rect(self.screen, WHITE, btn, 2)
        self.screen.blit(self.font.render("RESTART", True, WHITE), self.font.render("RESTART", True, WHITE).get_rect(center=btn.center))

        return btn, self.draw_exit_button()

    def run(self):
        running = True
        music_playing = False
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "menu":
                        btn, ex = self.draw_menu()
                        if btn.collidepoint(event.pos):
                            self.state = "playing"
                            self.reset_game()
                            # Start music when game starts
                            if not music_playing:
                                self.start_background_music()
                                music_playing = True
                        elif ex.collidepoint(event.pos):
                            running = False
                    elif self.state == "playing":
                        ex = self.draw_game()
                        if ex.collidepoint(event.pos):
                            running = False
                        else:
                            self.ball.switch_gravity()
                    elif self.state == "game_over":
                        btn, ex = self.draw_game_over()
                        if btn.collidepoint(event.pos):
                            self.state = "playing"
                            self.reset_game()
                            # Restart music when restarting game
                            if not music_playing:
                                self.start_background_music()
                                music_playing = True
                        elif ex.collidepoint(event.pos):
                            running = False
                elif event.type == pygame.KEYDOWN:
                    pass

            if self.state == "playing":
                # Check if music is still playing, restart if needed
                if self.music_loaded and not pygame.mixer.music.get_busy():
                    self.start_background_music()
                    
                self.ball.update()
                for s in self.spikes[:]:
                    s.update(self.speed)
                    if s.x < -s.width:
                        self.spikes.remove(s)
                        self.score += 10
                self.spike_timer += 1
                if self.spike_timer > random.randint(90, 150):
                    self.generate_spike_pattern()
                    self.spike_timer = 0
                if self.check_collisions():
                    self.state = "game_over"
                    # Stop music when game ends
                    self.stop_background_music()
                    music_playing = False
                self.update_difficulty()
            elif self.state == "game_over":
                # Make sure music is stopped during game over
                if music_playing:
                    self.stop_background_music()
                    music_playing = False

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "playing":
                self.draw_game()
            else:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        # Clean up
        self.stop_background_music()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
