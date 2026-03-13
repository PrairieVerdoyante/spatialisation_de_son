
# -----------------------------

# Lance un son qui "tourne" autour de l'utilisateur via les 4 enceintes.
# Délai entre le visuel et le son

# -----------------------------

#!/usr/bin/env python3
import time
import math
from vpython import sphere, vector, rate, scene
from soco import SoCo

# -----------------------------

# Configuration des enceintes

# -----------------------------
SPEAKERS =  [
    '192.168.123.66', # fl,
    '192.168.123.34' # fr
    '192.168.123.4', #rl
    '192.168.123.198',# rr
]



SPEAKERS = {
    "Front Gauche": '192.168.123.66',
    "Front Droite": '192.168.123.34',
    "Rear Gauche": '192.168.123.4',
    "Rear Droite": '192.168.123.198'
}

URI = "x-file-cifs://PC-SARAH/SonosMusic/piano_sound.wav"
BASE_VOLUME = 5
MAX_VOLUME = 15
RAYON = 3
VITESSE = 0.5

# -----------------------------

# Utilitaire : magnitude

# -----------------------------

def mag(v):
    return math.sqrt(v.x**2 + v.y**2 + v.z**2)

# -----------------------------

# Connexion aux enceintes

# -----------------------------

players = []
# SPEAKERS is a dict name->ip, iterate its items
for name, ip in SPEAKERS.items():
    try:
        device = SoCo(ip)
        try:
            device.unjoin()  # contrôle indépendant
        except Exception:
            pass
        device.volume = BASE_VOLUME
        device.clear_queue()
        device.play_uri(URI)
        players.append((name, device))
        print(f"[OK] Connecté : {name}")
    except Exception as e:
        print(f"[ERREUR] Impossible de connecter {name}: {e}")

if players:
    master = players[0][1]
    for name, device in players[1:]:
        try:
            device.join(master)
        except Exception as e:
            print(f"[WARN SYNC] {name}: {e}")
else:
    print("Aucune enceinte connectée, arrêt.")
    exit(1)

# -----------------------------

# Scène VPython

# -----------------------------

scene.title = "Simulation Audio Spatial"
scene.background = vector(0.1, 0.1, 0.1)
scene.width = 800
scene.height = 600
ball = sphere(radius=0.3, color=vector(0, 0.5, 1), make_trail=True)

# Positions virtuelles des enceintes (x,z)

speaker_positions = {
    "Front Gauche": vector(-2, 0, 2),
    "Front Droite": vector(2, 0, 2),
    "Rear Gauche": vector(-2, 0, -2),
    "Rear Droite": vector(2, 0, -2),
}

# -----------------------------

# Calcul du volume simulant spatialisation

# -----------------------------

def update_volumes(ball_pos):
    for name, device in players:
        spk_pos = speaker_positions.get(name)
        if not spk_pos:
            continue

        # distance et gain relatif
        distance = mag(ball_pos - spk_pos)
        gain = max(0, 1 - distance / 5)  # attenuation avec distance

        # calcul panning simple : plus proche sur X -> plus fort volume relatif
        dx = ball_pos.x - spk_pos.x
        panning = max(0, 1 - abs(dx) / 5)  # simple facteur
        # combinaison distance + panning
        volume = int(BASE_VOLUME + gain * (MAX_VOLUME - BASE_VOLUME) * panning)

        try:
            device.volume = volume
        except Exception as e:
            print(f"[WARN] Volume {name}: {e}")

# -----------------------------

# Animation principale

# -----------------------------

t = 0
while True:
    rate(60)  # ~60 FPS
    # mouvement circulaire
    x = RAYON * math.cos(t * VITESSE)
    z = RAYON * math.sin(t * VITESSE)
    ball.pos = vector(x, 0, z)

    update_volumes(ball.pos)
    t += 0.02
