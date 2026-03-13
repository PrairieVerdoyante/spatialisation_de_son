# -----------------------------

# Arrête le son pour les 4 enceintes

# -----------------------------

#!/usr/bin/env python
import time
import math
from soco import SoCo

if __name__ == '__main__':
    sonos = SoCo('192.168.123.66')
    
    sonosGroup = [
        SoCo('192.168.123.66'),
        SoCo('192.168.123.4'),
        SoCo('192.168.123.34'),
        SoCo('192.168.123.198'),
    ]
    
    uri = "x-file-cifs://PC-SARAH/music/guitar.wav"
    for sonos in sonosGroup:
        sonos.stop()
