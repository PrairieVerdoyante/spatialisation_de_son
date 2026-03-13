from soco import SoCo

SPEAKER_IPS = [
    '192.168.123.4', #rl
    '192.168.123.198',# rr
    '192.168.123.66', # fl,
    '192.168.123.34' # fr
    ]


SPEAKERS = {
    "rear_left": SoCo('192.168.123.4'),
    "rear_right": SoCo('192.168.123.198'),
    "front_left": SoCo('192.168.123.66'),
    "front_right": SoCo('192.168.123.34'),
}

def get_speaker(name):
    """Retourne une enceinte Sonos à partir de son nom."""
    return SPEAKERS.get(name)