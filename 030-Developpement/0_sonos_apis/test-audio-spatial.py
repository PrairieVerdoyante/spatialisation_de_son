from soco import SoCo
import time

# Adresses IP des 4 enceintes
ips = ["192.168.123.66"] # sonos 1.
speakers = [SoCo(ip) for ip in ips]

def crossfade(volumes):
    for sp, vol in zip(speakers, volumes):
        sp.volume = vol

while True:
    crossfade([100, 0, 0, 0])  # Son sur A
    time.sleep(1)
    # crossfade([0, 100, 0, 0])  # Son sur B
    # time.sleep(1)
    # crossfade([0, 0, 100, 0])  # Son sur C
    # time.sleep(1)
    # crossfade([0, 0, 0, 100])  # Son sur D
    # time.sleep(1)
