"""Move a sphere inside a rectangle and map its position to 4 corner speaker volumes.

Usage notes:
- This is a prototype that runs without Sonos. If `soco` is installed and Sonos devices
  are reachable on the LAN, it will optionally discover up to 4 speakers (or use IPs
  provided in SPEAKER_IPS) and control their volume.
- Keys:
  - Arrow keys / WASD: move
  - P: play provided URL on all speakers (optional)
  - O: stop playback on all speakers (optional)
  - ESC / close window: quit

How mapping works:
- The rectangle is normalized to [0..1] x [0..1]. We use bilinear weights for the
  four corners: TL, TR, BL, BR. Each corner's weight is converted to 0..100 volume.

Notes about Sonos:
- This script attempts to import soco. If not available it will still run and print
  computed volumes; use `pip install soco` to enable Sonos control.
- To make Sonos play something, run a local HTTP server hosting an MP3/WAV and press P
  to have the script request `play_uri` on each discovered speaker. Sonos needs to
  access the file by LAN IP (not localhost).
"""

import threading
import time

try:
    import pygame
except Exception:
    print("pygame is required. Install with: pip install pygame")
    raise

try:
    from soco import SoCo
    from soco.discovery import discover
    HAVE_SOCO = True
except Exception:
    HAVE_SOCO = False

# Optional: specify speaker IPs (strings). If empty, the script will try discovery.
SPEAKER_IPS =  [
    '192.168.123.66', # fl,
    '192.168.123.34', # fr
    '192.168.123.4', #rl
    '192.168.123.198',# rr
]

# Optional: URL to play on all speakers when you press P. Keep empty to avoid auto-play.
DEFAULT_PLAY_URL = "x-file-cifs://PC-SARAH/SonosMusic/piano_sound.wav"


class SonosManager:
    def __init__(self):
        self.devices = []
        if not HAVE_SOCO:
            print("soco not found, Sonos control disabled.")
            return
        # If specific IPs provided, use them
        if SPEAKER_IPS:
            for ip in SPEAKER_IPS[:4]:
                try:
                    self.devices.append(SoCo(ip))
                except Exception as e:
                    print(f"Failed to connect to SoCo at {ip}: {e}")
        else:
            # try discovery (may return None)
            print("Discovering Sonos devices (this may take a few seconds)...")
            found = discover()
            if not found:
                print("No Sonos devices discovered.")
            else:
                # discovered is a set of SoCo instances; pick up to 4
                for d in list(found)[:4]:
                    self.devices.append(d)
        print(f"Sonos devices managed: {[getattr(d,'player_name',None) for d in self.devices]}")

    def set_volumes(self, volumes):
        """Set volumes on devices.

        volumes: list of int 0..100 in the same order as self.devices
        """
        if not HAVE_SOCO or not self.devices:
            print("SonosManager: no devices available; volumes would be:", volumes)
            return
        for dev, vol in zip(self.devices, volumes):
            try:
                dev.volume = (int(max(0, min(100, vol))))
            except Exception as exc:
                print(f"Failed to set volume on {getattr(dev,'player_name',dev)}: {exc}")

    def play_uri_all(self, uri):
        if not HAVE_SOCO or not self.devices:
            print("play_uri_all: no devices available")
            return

        # Recovery step: try to stop and unjoin devices to clear previous groups
        for d in self.devices:
            try:
                d.stop()
            except Exception as exc:
                print(f"Warning: stop failed on {getattr(d,'player_name',d)}: {exc}")
            try:
                d.unjoin()
            except Exception:
                pass

        # short delay to allow devices to process unjoin/stop
        time.sleep(0.6)

        # choose master (coordinator) and join others to it
        master = self.devices[0]
        for dev in self.devices[1:]:
            try:
                dev.join(master)
            except Exception as exc:
                print(f"Warning: failed to join {getattr(dev,'player_name',dev)} to master: {exc}")

        # play only on the master (coordinator)
        try:
            master.play_uri(uri)
        except Exception as exc:
            print(f"Failed to play on master {getattr(master,'player_name',master)}: {exc}")

    def stop_all(self):
        if not HAVE_SOCO or not self.devices:
            return
        for dev in self.devices:
            try:
                dev.stop()
            except Exception:
                pass


def compute_corner_weights(x_norm, y_norm):
    """Return weights for TL, TR, BL, BR given normalized coordinates (0..1).

    y_norm: 0 at top, 1 at bottom (screen coordinates)
    """
    # bilinear weights
    w_tl = (1 - x_norm) * (1 - y_norm)
    w_tr = x_norm * (1 - y_norm)
    w_bl = (1 - x_norm) * y_norm
    w_br = x_norm * y_norm
    return [w_tl, w_tr, w_bl, w_br]


def main():
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Move Sphere -> 4 corner speaker mapping')
    clock = pygame.time.Clock()

    rect_margin = 80
    rect = pygame.Rect(rect_margin, rect_margin, WIDTH - rect_margin * 2, HEIGHT - rect_margin * 2)
    radius = 16
    pos = pygame.Vector2(rect.centerx, rect.centery)
    speed = 300.0  # pixels / second

    sonos = SonosManager()

    playing_url = DEFAULT_PLAY_URL

    show_debug = True

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    if playing_url:
                        print("Playing", playing_url)
                        # run play in background to not block game
                        threading.Thread(target=sonos.play_uri_all, args=(playing_url,), daemon=True).start()
                    else:
                        print("No DEFAULT_PLAY_URL configured. Set DEFAULT_PLAY_URL to a reachable HTTP URL.")
                elif event.key == pygame.K_o:
                    threading.Thread(target=sonos.stop_all, daemon=True).start()

        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move.y += 1

        if move.length_squared() > 0:
            move = move.normalize()
            pos += move * speed * dt

        # clamp inside rect
        pos.x = max(rect.left + radius, min(rect.right - radius, pos.x))
        pos.y = max(rect.top + radius, min(rect.bottom - radius, pos.y))

        # normalized coords
        x_norm = (pos.x - rect.left) / rect.width
        y_norm = (pos.y - rect.top) / rect.height

        weights = compute_corner_weights(x_norm, y_norm)
        # convert to 0..100 volumes
        volumes = [int(w * 100) for w in weights]

        # Update sonos volumes (non-blocking)
        threading.Thread(target=sonos.set_volumes, args=(volumes,), daemon=True).start()

        # draw
        screen.fill((30, 30, 30))
        pygame.draw.rect(screen, (60, 60, 60), rect)
        # corners markers
        corner_positions = [
            (rect.left + 10, rect.top + 10),  # TL
            (rect.right - 10, rect.top + 10),  # TR
            (rect.left + 10, rect.bottom - 10),  # BL
            (rect.right - 10, rect.bottom - 10),  # BR
        ]
        colors = [(200, 50, 50), (50, 200, 50), (50, 50, 200), (200, 200, 50)]
        for (cx, cy), c in zip(corner_positions, colors):
            pygame.draw.circle(screen, c, (int(cx), int(cy)), 8)

        pygame.draw.circle(screen, (240, 120, 120), (int(pos.x), int(pos.y)), radius)

        if show_debug:
            font = pygame.font.SysFont(None, 20)
            lines = [
                f"x={x_norm:.2f} y={y_norm:.2f}",
                f"Volumes TL/TR/BL/BR: {volumes}",
                f"Sonos devices: {len(sonos.devices)} (keys: P play, O stop)",
            ]
            for i, line in enumerate(lines):
                surf = font.render(line, True, (220, 220, 220))
                screen.blit(surf, (10, 10 + i * 18))

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
