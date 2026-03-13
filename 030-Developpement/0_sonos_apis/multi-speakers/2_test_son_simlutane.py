#!/usr/bin/env python
import time
from soco import SoCo
import math

# Liste d'enceintes Sonos
SPEAKERS = [
    #'192.168.123.4', #rl
    #'192.168.123.198',# rr
    '192.168.123.66', # fl,
    '192.168.123.34' # fr
    ]


URI = "x-file-cifs://PC-SARAH/music/piano_sound.wav"

BASE_VOLUME = 5
MAX_VOLUME = 15
PERIOD = 5  # en secondes

if __name__ == '__main__':
    # 1. Définir le coordinateur (première enceinte)
    coordinator_name, coordinator_ip = SPEAKERS[0]
    coordinator = SoCo(coordinator_ip)
    print(f"[INFO] Coordinateur = {coordinator_name}")
    
    # 2. Ajouter les autres enceintes au groupe
    for name, ip in SPEAKERS[1:]:
        speaker = SoCo(ip)
        print(f"[INFO] Ajout de {name} au groupe...")
        speaker.join(coordinator)

    # 3. Configurer la lecture
    coordinator.clear_queue()
    coordinator.play_uri(URI)

    # 4. Synchronisation dynamique du volume (facultatif)
    start_time = time.time()
    while True:
        current_time = time.time() - start_time
        gain = (math.sin(2 * math.pi * current_time / PERIOD) + 1) / 2
        volume = int(BASE_VOLUME + gain * (MAX_VOLUME - BASE_VOLUME))
        # Le volume de groupe peut être modifié via le coordinateur
        coordinator.group.volume = volume
        print(f"Volume du groupe : {volume}")
        time.sleep(0.1)
