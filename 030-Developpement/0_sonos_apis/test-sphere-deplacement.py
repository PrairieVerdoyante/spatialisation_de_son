#!/usr/bin/env python
import time
import math
from vpython import sphere, vector, rate, scene
from soco import SoCo

# -----------------------------
# Configuration des enceintes
# -----------------------------
SPEAKERS = [
    ("Front Gauche", "192.168.123.60"),
    ("Front Droite", "192.168.123.61"),
    ("Rear Gauche", "192.168.123.62"),
    ("Rear Droite", "192.168.123.63"),
]

URI = "x-file-cifs://PC-SARAH/SonosMusic/piano_sound.wav"
BASE_VOLUME = 5   # volume minimum
MAX_VOLUME = 40   # volume maximum
RAYON = 3         # rayon du cercle de rotation de la sphère
VITESSE = 0.5     # vitesse de rotation

# Connexion aux enceintes
players = []
for name, ip in SPEAKERS:
    try:
        device = SoCo(ip)
        device.volume = BASE_VOLUME
        device.clear_queue()
        device.play_uri(URI)
        players.append((name, device))
        print(f"[OK] Connecté à {name} ({ip})")
    except Exception as e:
        print(f"[ERREUR] Impossible de connecter {name} ({ip}): {e}")

# -----------------------------
# Scène 3D
# -----------------------------
scene.title = "Sphère 3D avec Audio Spatial Sonos"
scene.background = vector(0.1, 0.1, 0.1)
scene.width = 800
scene.height = 600

ball = sphere(radius=0.3, color=vector(0, 0.5, 1), make_trail=True)

# Position fixe des enceintes (en 3D virtuelle)
speaker_positions = {
    "Front Gauche": vector(-2, 0, 2),
    "Front Droite": vector(2, 0, 2),
    "Rear Gauche": vector(-2, 0, -2),
    "Rear Droite": vector(2, 0, -2),
}

# -----------------------------
# Fonction pour ajuster volume
# -----------------------------
def update_volumes(ball_pos):
    for name, device in players:
        spk_pos = speaker_positions[name]
        distance = mag(ball_pos - spk_pos)
        # Inversion de la distance (plus proche = plus fort)
        gain = max(0, 1 - distance / 5)
        volume = int(BASE_VOLUME + gain * (MAX_VOLUME - BASE_VOLUME))
        device.volume = volume

# -----------------------------
# Animation principale
# -----------------------------
t = 0
while True:
    rate(60)  # 60 FPS
    x = RAYON * math.cos(t * VITESSE)
    z = RAYON * math.sin(t * VITESSE)
    ball.pos = vector(x, 0, z)

    update_volumes(ball.pos)
    t += 0.02
