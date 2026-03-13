# Recovers speakers and removes them from unwanted groups
from soco import SoCo
IPS = [
    '192.168.123.66',
    '192.168.123.34',
    '192.168.123.4',
    '192.168.123.198',
]
for ip in IPS:
    try:
        s = SoCo(ip)
        print('Stopping', getattr(s, 'player_name', ip))
        try:
            s.stop()
        except Exception as e:
            print(' stop failed:', e)
        try:
            s.unjoin()   # leave any group
        except Exception as e:
            print(' unjoin failed (maybe already ungrouped):', e)
    except Exception as e:
        print('Cannot contact', ip, e)
print('Recovery commands sent. Wait 1-2s then try playback.')