#!/usr/bin/env python3
import time
import math
from vpython import sphere, vector, rate, scene
from soco import SoCo

# -----------------------------
# Configuration des enceintes
# -----------------------------


SPEAKERS = {
    #("Rear Gauche", '192.168.123.4'),
    #("Rear Droite", '192.168.123.198'),
    ("Front Gauche", '192.168.123.66'),
    ("Front Droite", '192.168.123.34'),
}

URI = "x-file-cifs://PC-SARAH/SonosMusic/piano_sound.wav"
BASE_VOLUME = 5   # volume minimum
MAX_VOLUME = 10   # volume maximum
RAYON = 3         # rayon du cercle de rotation de la sphère
VITESSE = 0.5     # vitesse de rotation

# -----------------------------
# Fonction utilitaire : magnitude
# -----------------------------
def mag(v):
    return math.sqrt(v.x**2 + v.y**2 + v.z**2)

# -----------------------------
# Connexion aux enceintes
# -----------------------------
players = []
for name, ip in SPEAKERS:
    try:
        device = SoCo(ip)

        # Dégrouper pour contrôle indépendant
        try:
            device.unjoin()
        except Exception:
            pass

        device.volume = BASE_VOLUME
        device.clear_queue()
        device.play_uri(URI)

        players.append((name, device))
        print(f"[OK] Connecté et initialisé : {name} ({ip})")
    except Exception as e:
        print(f"[ERREUR] Impossible de connecter {name} ({ip}): {e}")

# -----------------------------
# Synchronisation des enceintes (lecture en même temps)
# -----------------------------
if players:
    master_device = players[0][1]  # première enceinte = maître
    for name, device in players[1:]:
        try:
            device.join(master_device)
            print(f"[SYNC] {name} rejoint {players[0][0]}")
        except Exception as e:
            print(f"[ERREUR SYNC] {name}: {e}")
else:
    print("Aucune enceinte connectée, arrêt du script.")
    exit(1)

# -----------------------------
# Scène 3D
# -----------------------------
scene.title = "Simulation Audio : Sphère en Mouvement"
scene.background = vector(0.1, 0.1, 0.1)
scene.width = 800
scene.height = 600
ball = sphere(radius=0.3, color=vector(0, 0.5, 1), make_trail=True)

# Positions virtuelles des enceintes
speaker_positions = {
    "Front Gauche": vector(-2, 0, 2),
    "Front Droite": vector(2, 0, 2),
    "Rear Gauche": vector(-2, 0, -2),
    "Rear Droite": vector(2, 0, -2),
}

# -----------------------------
# Gestion dynamique des volumes
# -----------------------------
def update_volumes(ball_pos):
    for name, device in players:
        spk_pos = speaker_positions.get(name)
        if not spk_pos:
            continue
        distance = mag(ball_pos - spk_pos)
        gain = max(0, 1 - distance / 5)
        volume = int(BASE_VOLUME + gain * (MAX_VOLUME - BASE_VOLUME))
        try:
            device.volume = volume
        except Exception as e:
            print(f"[WARN] Impossible de changer le volume de {name}: {e}")

# -----------------------------
# Animation principale
# -----------------------------
t = 0
while True:
    rate(60)
    x = RAYON * math.cos(t * VITESSE)
    z = RAYON * math.sin(t * VITESSE)
    ball.pos = vector(x, 0, z)
    update_volumes(ball.pos)
    t += 0.02
