import pygame
import math
import time
import socket

class FittsLawTest:
    def __init__(self, num_circles=8, num_trials=16, fps=60, width=1250, height=750):
        self.width = width 
        self.height = height 

        # gameplay parameters
        self.BLACK = (0,0,0)
        self.RED   = (255,0,0)
        self.YELLOW = (255,255,0)
        self.BLUE   = (0,102,204)
        self.small_rad = 40
        self.big_rad   = 275
        self.pos_factor1 = self.big_rad/2
        self.pos_factor2 = (self.big_rad * math.sqrt(3))//2

        self.done = False
        self.VEL = 20
        self.dwell_time = 3
        self.num_of_circles = num_circles 
        self.max_trial = num_trials
        self.width = width
        self.height = height
        self.fps = fps
        self.trial = 0
        self.cursor_size = 14

        # interface objects
        self.circles = []
        self.cursor = pygame.Rect(self.width//2 - 7, self.height//2 - 7, self.cursor_size, self.cursor_size)
        self.goal_circle = -1
        self.get_new_goal_circle()
        self.current_direction = [0,0]


    def draw(self):
        self.screen.fill(self.BLACK)
        self.draw_circles()
        self.draw_cursor()
        self.draw_timer()
    
    def draw_circles(self):
        if not len(self.circles):
            self.angle = 0
            self.angle_increment = 360 // self.num_of_circles
            while self.angle < 360:
                self.circles.append(pygame.Rect((self.width//2 - self.small_rad) + math.cos(math.radians(self.angle)) * self.big_rad, (self.height//2 - self.small_rad) + math.sin(math.radians(self.angle)) * self.big_rad, self.small_rad * 2, self.small_rad * 2))
                self.angle += self.angle_increment

        for circle in self.circles:
            pygame.draw.circle(self.screen, self.RED, (circle.x + self.small_rad, circle.y + self.small_rad), self.small_rad, 2)
        
        goal_circle = self.circles[self.goal_circle]
        pygame.draw.circle(self.screen, self.RED, (goal_circle.x + self.small_rad, goal_circle.y + self.small_rad), self.small_rad)
            
    def draw_cursor(self):
        pygame.draw.circle(self.screen, self.YELLOW, (self.cursor.x + 7, self.cursor.y + 7), 7)

    def draw_timer(self):
        if hasattr(self, 'dwell_timer'):
            if self.dwell_timer is not None:
                toc = time.perf_counter()
                duration = round((toc-self.dwell_timer),2)
                time_str = str(duration)
                draw_text = self.font.render(time_str, 1, self.BLUE)
                self.screen.blit(draw_text, (10, 10))

    def update_game(self):
        self.draw()
        self.run_game_process()
        self.move()
    
    def run_game_process(self):
        self.check_collisions()
        self.check_events()

    def check_collisions(self):
        circle = self.circles[self.goal_circle]
        if math.sqrt((circle.centerx - self.cursor.centerx)**2 + (circle.centery - self.cursor.centery)**2) < (circle[2]/2 + self.cursor[2]/2):
            pygame.event.post(pygame.event.Event(pygame.USEREVENT + self.goal_circle))
            self.Event_Flag = True
        else:
            pygame.event.post(pygame.event.Event(pygame.USEREVENT + self.num_of_circles))
            self.Event_Flag = False

    def check_events(self):
        # closing window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.current_direction[0] -= self.VEL
                elif event.key == pygame.K_RIGHT:
                    self.current_direction[0] += self.VEL
                elif event.key == pygame.K_UP:
                    self.current_direction[1] -= self.VEL
                elif event.key == pygame.K_DOWN:
                    self.current_direction[1] += self.VEL
            
        self.current_direction = [0,0]
        data, _ = self.sock.recvfrom(1024)
        data = str(data.decode("utf-8"))
        if data:
            input_class = float(data.split(' ')[0])
            velocity = float(data.split(' ')[1])
            # 0 = Hand Closed
            if input_class == 1:
                self.current_direction[0] -= self.VEL * velocity
            # 1 = Hand Open
            elif input_class == 2:
                self.current_direction[0] += self.VEL * velocity
            # 3 = Pronation 
            elif input_class == 4:
                self.current_direction[1] -= self.VEL * velocity
            # 4 = Supination
            elif input_class == 3:
                self.current_direction[1] += self.VEL * velocity
            

            ## CHECKING FOR COLLISION BETWEEN CURSOR AND RECTANGLES
            if event.type >= pygame.USEREVENT and event.type < pygame.USEREVENT + self.num_of_circles:
                if self.dwell_timer is None:
                    self.dwell_timer = time.perf_counter()
                else:
                    toc = time.perf_counter()
                    self.duration = round((toc - self.dwell_timer), 2)
                if self.duration >= self.dwell_time:
                    self.get_new_goal_circle()
                    self.dwell_timer = None
                    if self.trial < self.max_trial-1: # -1 because max_trial is 1 indexed
                        self.trial += 1
                    else:
                        self.done = True
            elif event.type == pygame.USEREVENT + self.num_of_circles:
                if self.Event_Flag == False:
                    self.dwell_timer = None
                    self.duration = 0

    def move(self):
        # Making sure its within the bounds of the screen
        if self.cursor.x + self.current_direction[0] > 0 + self.cursor_size//2 and self.cursor.x + self.current_direction[0] + self.cursor_size//2 < self.width:
            self.cursor.x += self.current_direction[0]
        if self.cursor.y + self.current_direction[1] > 0 + self.cursor_size//2 and self.cursor.y + self.current_direction[1] + self.cursor_size//2 < self.height:
            self.cursor.y += self.current_direction[1]
    
    def get_new_goal_circle(self):
        if self.goal_circle == -1:
            self.goal_circle = 0
            self.next_circle_in = self.num_of_circles//2
            self.circle_jump = 0
        else:
            self.goal_circle =  (self.goal_circle + self.next_circle_in )% self.num_of_circles
            if self.circle_jump == 0:
                self.next_circle_in = self.num_of_circles//2 + 1
                self.circle_jump = 1
            else:
                self.next_circle_in = self.num_of_circles // 2
                self.circle_jump = 0

    def run(self):
        pygame.init()
        self.font = pygame.font.SysFont('helvetica', 40)
        self.screen = pygame.display.set_mode([self.width, self.height])
        self.clock = pygame.time.Clock()

        # Socket for reading EMG
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.bind(('127.0.0.1', 12346))

        while not self.done:
            # updated frequently for graphics & gameplay
            self.update_game()
            pygame.display.update()
            self.clock.tick(self.fps)
        pygame.quit()