import pygame
import time 
import numpy as np
import socket
import os 

def handle_emg(sock):
    try:
        data, _ = sock.recvfrom(1024)
    except:
        return None 
    
    data = str(data.decode("utf-8"))
    if data:
        input_class = float(data.split(' ')[0])
        if input_class != 0:
            return input_class - 1
    return -1

TEST_TIME = 120
MAX_SPEED = 7.5
MIN_SPEED = 2.5
MIN_TIME = 0.6
MAX_TIME = 2.2

log = {
    "times": [],
    "notes": [],
    "button_pressed": [],
    "score": []
}

class Note:
    def __init__(self, type):
        self.type = type 
        assert self.type in [0,1,2,3]
        y_poses = [75, 200, 325, 450]
        colors = [(255, 0, 0),(0, 255, 0),(0, 0, 255),(255, 165, 0)]
        # Based on the type, set up the note 
        self.x_pos = y_poses[self.type]          
        self.y_pos = 0
        self.color = colors[self.type]
        self.length = 35 * (5 * np.random.random()) # Random integer between 1 and 5
        self.hit = False  # Track if note has been initially hit
        self.hold_points_collected = 0  # Track points collected while holding
        self.max_hold_points = int(self.length)  # Maximum points possible from holding

    def move_note(self, speed=5):
        self.y_pos += speed
        if self.y_pos > 1000:
            return -1
        return 0
    
    def check_hit(self, key_pressed, target_y=500):
        points = 0
        # Initial hit detection
        if not self.hit and self.type == key_pressed:
            distance = abs(self.y_pos - target_y)
            if distance <= 30:
                self.hit = True
                points += 100  # Perfect initial hit
            elif distance <= 60:
                self.hit = True
                points += 50   # Good initial hit

        # Hold note scoring
        if self.hit and self.type == key_pressed:
            # Check if player is holding through the note length
            note_top = self.y_pos - 60 - self.length
            note_bottom = self.y_pos
            if target_y >= note_top and target_y <= note_bottom:
                # Award points for holding, limited by max_hold_points
                if self.hold_points_collected < self.max_hold_points:
                    hold_points = 2  # Points per frame while holding
                    self.hold_points_collected += hold_points
                    points += hold_points

        return points


def start_game():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init() 
    pygame.display.set_caption('Testing Environment')
    font = pygame.font.SysFont('Comic Sans MS', 30)
    score_font = pygame.font.SysFont('Comic Sans MS', 40)
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode([525, 700])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    sock.bind(('127.0.0.1', 12346))
    sock.setblocking(0)

    last_note = time.time()
    start_time = time.time() + TEST_TIME

    notes = []
    key_pressed = -1
    score = 0
    combo = 0

    # Run until the user asks to quit
    running = True
    while running:
        clock.tick(60)

        gen_time = ((start_time - time.time())/TEST_TIME) * (MAX_TIME - MIN_TIME) + MIN_TIME
        if time.time() - last_note > gen_time: # Generation
            new_note = np.random.randint(0,4)
            notes.append(Note(new_note))
            last_note = time.time()

        if start_time - time.time() <= 0:
            running = False

        # Fill the background with white
        screen.fill((255, 255, 255))

        # Update time remaining 
        text = font.render('{0:.1f}'.format(start_time - time.time()), True, (0,0,0))
        textRect = text.get_rect()
        textRect.center = (470, 25)
        screen.blit(text, textRect)

        # Display score
        score_text = score_font.render(f'Score: {score}', True, (0,0,0))
        score_rect = score_text.get_rect()
        score_rect.center = (200, 25)
        screen.blit(score_text, score_rect)

        # Display combo if > 0
        if combo > 1:
            combo_text = font.render(f'Combo x{combo}!', True, (255,0,0))
            combo_rect = combo_text.get_rect()
            combo_rect.center = (200, 60)
            screen.blit(combo_text, combo_rect)

        # Did the user click the window close button?
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Deal with key presses 
        current_frame_keys = set()
        
        val = handle_emg(sock)
        if val != None and val != key_pressed:
            key_pressed = val
            current_frame_keys.add(val)

        # Draw notes on bottom of screen 
        pygame.draw.circle(screen, (255, 0, 0), (75, 500), 35, width=8 - (key_pressed==0) * 8)
        pygame.draw.circle(screen, (0, 255, 0), (200, 500), 35, width=8  - (key_pressed==1) * 8)
        pygame.draw.circle(screen, (0, 0, 255), (325, 500), 35, width=8  - (key_pressed==2) * 8)
        pygame.draw.circle(screen, (255, 165, 0), (450, 500), 35, width=8  - (key_pressed==3) * 8)

        # Move and deal with notes coming down 
        hit_this_frame = False
        for n in notes:
            speed = (1 - (start_time - time.time())/TEST_TIME) * (MAX_SPEED - MIN_SPEED) + MIN_SPEED
            if n.move_note(speed=speed) == -1:
                notes.remove(n)
                if not n.hit:  # Only break combo if note wasn't hit at all
                    combo = 0
                continue

            # Check for note hits and update score
            points = n.check_hit(key_pressed)
            if points > 0:
                hit_this_frame = True
                if points >= 50:  # Only increase combo on initial hits, not hold points
                    combo += 1
                score += points * (combo // 5 + 1)  # Bonus points for higher combos

            # Draw the note
            w = 0
            if n.type == key_pressed and n.y_pos >= 500 and n.y_pos - 60 - n.length <= 500:
                w = 5
            pygame.draw.circle(screen, n.color, (n.x_pos, n.y_pos), 35, width=w)
            pygame.draw.rect(screen, n.color, (n.x_pos - 20, n.y_pos - 30 - n.length, 40, n.length), width=w)
            pygame.draw.circle(screen, n.color, (n.x_pos, n.y_pos - 60 - n.length), 35, width=w)

        # Break combo if pressing wrong buttons
        if not hit_this_frame and key_pressed != -1:
            combo = 0

        pygame.draw.rect(screen, (255,255,255), (0, 550, 1000, 300))

        # Log everything 
        log['times'].append(time.time())
        log['notes'].append([[n.type, n.y_pos, n.length] for n in notes])
        log['button_pressed'].append(key_pressed)
        log['score'].append(score)
        
        # Flip the display
        pygame.display.flip()

    # Done! Time to quit.
    pygame.quit()