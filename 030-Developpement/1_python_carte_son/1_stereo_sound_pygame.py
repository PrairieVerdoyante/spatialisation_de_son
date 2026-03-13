"""
pygame_pan.py
Déplacement horizontal d'un point (A/D) avec panoramique audio (2 sorties) avec Pygame.
NOTE:   brancher chaque sortie séparément sur les LINE OUPUT de la carte.
        Si les outputs sont en stéréo, il est possible de les brancher sur la sortie PHONES sur le devant de la carte. Ne pas oublier de monter légèrement le son
"""

import pygame
import numpy as np
import sounddevice as sd

# -------------------------
# AUDIO CONFIG
# -------------------------
DEVICE_ID = 13  #  13 Line (2- Steinberg UR44C), Windows WASAPI (0 in, 2 out) - Line Output 2
fs = 44100
frequency = 440
amplitude = 0.3
buffer_size = 1024
phase = 0.0

pygame.mixer.quit()
pygame.display.init()

# -------------------------
# PYGAME CONFIG
# -------------------------
pygame.init()
WIDTH, HEIGHT = 800, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Panoramique Mono L/R (A/D)")

clock = pygame.time.Clock()

x = WIDTH // 2
y = HEIGHT // 2
speed = 5
running = True

# -------------------------
# AUDIO CALLBACK
# -------------------------
def audio_callback(outdata, frames, time, status):
    global phase, x

    t = (np.arange(frames) + phase) / fs
    mono = amplitude * np.sin(2 * np.pi * frequency * t)
    phase += frames

    # Contrôle direct des deux sorties
    pan = x / WIDTH
    left = mono * np.sqrt(1 - pan)
    right = mono * np.sqrt(pan)

    outdata[:] = np.column_stack((left, right))

# -------------------------
# AUDIO STREAM
# -------------------------
stream = sd.OutputStream(
    device=DEVICE_ID,
    samplerate=fs,
    blocksize=buffer_size,
    channels=2,
    callback=audio_callback
)
stream.start()

# -------------------------
# MAIN LOOP
# -------------------------
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        x -= speed
    if keys[pygame.K_d]:
        x += speed

    x = max(0, min(WIDTH, x))

    # DRAW
    screen.fill((30, 30, 30))
    pygame.draw.circle(screen, (0, 200, 255), (x, y), 10)
    pygame.display.flip()

# -------------------------
# CLEANUP
# -------------------------
stream.stop()
stream.close()
pygame.quit()