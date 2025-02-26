import pygame
import random
import socket
from pygame.locals import *
from collections import deque

class SnakeGame:
    def __init__(self):
        random.seed(0)
        self.width = 500
        self.height = 500
        
        # Game Variables:
        self.running = True 
        self.score = 0
        self.movement = 1
        self.snake_head = [40, 40]
        self.snake_body = []
        self.target = [None, None]
        self.generate_target()
        
        # Replace unlimited list with a fixed-size deque
        self.max_history = 1000  # More than enough for any reasonable snake length
        self.previous_key_presses = deque(maxlen=self.max_history)
        self.current_direction = "right"  # Default direction
        
        # Add keyboard controls
        self.key_mapping = {
            K_LEFT: "left",
            K_RIGHT: "right",
            K_UP: "up",
            K_DOWN: "down"
        }

        # Colors
        self.snake_green = (5, 255, 0)
        self.head_blue = (0, 133, 255)
        self.red = (255, 0, 0)

    def generate_target(self):
        x = random.randrange(20, self.width-20) 
        y = random.randrange(20, self.height-20) 
        self.target[0] = x - x % self.movement
        self.target[1] = y - y % self.movement
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key in self.key_mapping:
                    self.current_direction = self.key_mapping[event.key]
                    self.previous_key_presses.append(self.current_direction)
                    self.move_snake()
    
    def handle_emg(self):
        try:
            data, _ = self.sock.recvfrom(1024)
            data_str = data.decode("utf-8")
            
            try:
                input_class = float(data_str.split(' ')[0])
                
                new_direction = None
                # Map EMG signals to directions
                if input_class == 1:
                    new_direction = "left"
                elif input_class == 2:
                    new_direction = "right"
                elif input_class == 3:
                    new_direction = "down"
                elif input_class == 4:
                    new_direction = "up"
                
                if new_direction:
                    self.current_direction = new_direction
                    self.previous_key_presses.append(new_direction)
                    self.move_snake()
            except (ValueError, IndexError):
                # Handle invalid data format
                pass
                
        except BlockingIOError:
            # No data available, not an error
            pass
        except Exception as e:
            # Log other exceptions
            print(f"EMG error: {e}")
    
    def move_snake(self):
        # Always store the current position before moving
        old_positions = [self.snake_head.copy()]
        for segment in self.snake_body:
            old_positions.append(segment.copy())
        
        # Move head using current direction
        self.move(self.current_direction, self.snake_head)
        
        # Move body segments to previous positions of segments ahead of them
        for i in range(len(self.snake_body)):
            self.snake_body[i][0] = old_positions[i][0]
            self.snake_body[i][1] = old_positions[i][1]

    def move(self, direction, block):
        block_temp = block.copy()
        if direction == "left":
            block_temp[0] -= self.movement
        elif direction == "right":
            block_temp[0] += self.movement
        elif direction == "up":
            block_temp[1] -= self.movement
        elif direction == "down":
            block_temp[1] += self.movement
        
        # Check boundaries
        if (block_temp[0] > 0 and block_temp[0] < self.width and 
            block_temp[1] > 0 and block_temp[1] < self.height):
            block[0] = block_temp[0]
            block[1] = block_temp[1]

    def grow_snake(self):
        # Grow the snake by multiple segments at once
        for _ in range(3):
            # Get the position of the last segment (or head if no segments)
            if len(self.snake_body) > 0:
                new_segment = self.snake_body[-1].copy()
            else:
                new_segment = self.snake_head.copy()
                
            # Add the direction to the history for future reference
            self.previous_key_presses.append(self.current_direction)
            
            # Place the new segment opposite to the current direction
            if self.current_direction == "left":
                new_segment[0] += self.movement
            elif self.current_direction == "right":
                new_segment[0] -= self.movement
            elif self.current_direction == "up":
                new_segment[1] += self.movement
            elif self.current_direction == "down":
                new_segment[1] -= self.movement
                
            self.snake_body.append(new_segment)

    def run_game(self):
        # Pygame Setup:
        pygame.init()
        self.window = pygame.display.set_mode([self.width, self.height])
        pygame.display.set_caption('Pygame (Snake) EMG Demo')
        self.clock = pygame.time.Clock()

        # Socket for reading EMG
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.sock.bind(('127.0.0.1', 12346))
        self.sock.setblocking(0)
        
        # Initialize with a default direction
        self.previous_key_presses.append(self.current_direction)

        while self.running: 
            # Fill the background
            self.window.fill((233, 233, 233))

            # Handle keyboard events
            self.handle_events()
            
            # Handle EMG input
            self.handle_emg()
            
            # Auto-movement: move snake in current direction each frame
            # This makes the game playable even with input lag
            if len(self.previous_key_presses) > 0:
                self.move_snake()

            # Check for collision between snake and target
            snake = Rect(self.snake_head[0], self.snake_head[1], 20, 20)
            target = Rect(self.target[0], self.target[1], 20, 20)
            if pygame.Rect.colliderect(snake, target):
                self.generate_target()
                self.grow_snake()
                self.score += 1

            # Draw Snake
            pygame.draw.rect(self.window, self.head_blue, snake, border_radius=2)
            for b in self.snake_body:
                pygame.draw.rect(self.window, self.snake_green, [b[0], b[1], 20, 20], border_radius=2)

            # Draw Target 
            pygame.draw.rect(self.window, self.red, target)

            # Score label
            myfont = pygame.font.SysFont("arial bold", 30)
            label = myfont.render("Score: " + str(self.score), 1, (0, 0, 0))
            self.window.blit(label, (self.width - 100, 10))

            pygame.display.update()
            self.clock.tick(120)

        pygame.quit()