# Plays a sound and varies its volume
#!/usr/bin/env python
import time
import math
from soco import SoCo

if __name__ == '__main__':
    sonos = SoCo('192.168.123.66')
    # avant gauche: 192.168.123.66
    # avant droite: 192.168.123.4
    # arrière gauche: 192.168.123.34
    # arrière droite: 192.168.123.198

    uri = "x-file-cifs://PC-SARAH/music/piano_sound.wav"

    # Jouer directement le fichier via URI
    sonos.clear_queue()
    sonos.play_uri(uri)
   #  sonos.play_from_queue(0)

    # Paramètres du volume dynamique
    start_time = time.time()
    period = 5         # durée d'un cycle complet de sinus (en secondes)
    base_volume = 10    # volume minimum
    max_volume = 30   # volume maximum

    while True:
        current_time = time.time() - start_time
        gain = (math.sin(2 * math.pi * current_time / period) + 1) / 2
        volume = int(base_volume + gain * (max_volume - base_volume))
        sonos.volume = volume
        time.sleep(0.1)  # éviter de spammer la Sonos
