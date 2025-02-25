import pygame
import random
import time
import socket

class OneDFitts:
    def __init__(self, width=1000, height=400, min_width=30, max_width=30, dwell_time=0.5, num_targets=50, random_seed=0):
        self.width = width
        self.height = height
        self.min_width = min_width
        self.max_width = max_width
        random.seed(random_seed)
        self.target = None
        self.cursor = {'x': self.width / 2, 'y': self.height / 2}
        self.dwell_time = dwell_time
        self.enter_time = None
        self.num_targets = num_targets
        self.VEL = 4

    def generate_target(self):
        new_target = Target()
        new_target.initialize_random(self.width, self.height, self.min_width, self.max_width)
        self.target = new_target

    def is_cursor_in_target(self):
        return self.cursor['x'] > self.target.x and self.cursor['x'] < self.target.x + self.target.width

    def start_game(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 12346))
        self.sock.setblocking(0)
        
        pygame.init()

        screen = pygame.display.set_mode([self.width, self.height])
        clock = pygame.time.Clock()

        self.generate_target()

        running = True
        while running:
            screen.fill((255, 255, 255))

            try:
                data, _ = self.sock.recvfrom(1024)

                data = str(data.decode("utf-8"))
                if data:
                    input_class = float(data.split(' ')[0])
                    if input_class == 1:
                        self.cursor['x'] += self.VEL
                    elif input_class == 2:
                        self.cursor['x'] -= self.VEL
            except:
                pass

            # Bound cursor within screen
            self.cursor['x'] = max(0, min(self.cursor['x'], self.width))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            if self.num_targets == 0:
                running = False

            time_left = ""
            if self.enter_time is not None:
                time_left = "{:.2f}".format(self.dwell_time - (time.time() - self.enter_time))
            my_font = pygame.font.SysFont(None, 30)
            text_surface = my_font.render(time_left, True, (0, 0, 0))
            screen.blit(text_surface, (10, 10))

            if self.target:
                if self.is_cursor_in_target():
                    pygame.draw.rect(screen, (75, 170, 200), (self.target.x, self.target.y, self.target.width, self.target.height))
                else:
                    pygame.draw.rect(screen, (0, 0, 255), (self.target.x, self.target.y, self.target.width, self.target.height))

                if self.is_cursor_in_target() and self.enter_time is None:
                    self.enter_time = time.time()
                elif not self.is_cursor_in_target():
                    self.enter_time = None

                if self.enter_time:
                    if time.time() - self.enter_time >= self.dwell_time:
                        self.enter_time = None
                        self.generate_target()
                        self.num_targets -= 1

            pygame.draw.circle(screen, (0, 0, 0), (self.cursor['x'], self.cursor['y']), 8)

            pygame.display.flip()

            clock.tick(240)

        pygame.quit()

class Target:
    def __init__(self, x=None, y=None, width=None, height=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def initialize_random(self, screen_width, screen_height, min_width, max_width):
        self.width = min_width + (max_width - min_width) * random.random()
        self.height = 150
        self.x = random.random() * screen_width - max_width
        if self.x < max_width:
            self.x = max_width + 10
        self.y = screen_height / 2 - self.height / 2