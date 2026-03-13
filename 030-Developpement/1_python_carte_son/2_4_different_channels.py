"""
Commande simple pour tester une scène 4.0 avec deux sorties stéréo séparées
(front / back) à l'aide de sounddevice + pygame.

Touches :
  A / D : panoramique gauche / droite
  W / S : balance avant / arrière
  ESC ou bouton fermer : quitter

Avant de lancer, adaptez les IDs des devices (front et back) à ceux retournés
par sd.query_devices(). Ici, on suppose :
  - 13 : Line (2- Steinberg UR44C)   -> stéréo avant
  - 4  : Line (2- Steinberg UR44C)   -> stéréo arrière
  
  N'a pas fonctionné.
"""

import numpy as np
import pygame
import sounddevice as sd
from threading import Lock


# -------------------------
# AUDIO CONFIG
# -------------------------
FRONT_DEVICE_ID = 13  # stéréo avant
REAR_DEVICE_ID = 4    # stéréo arrière
FS = 44100
FREQ = 440
AMP = 0.25
BLOCK = 512


# État partagé pour les callbacks audio
state = {
	"phase": 0,
	"pan": 0.5,    # 0 = gauche, 1 = droite
	"depth": 0.5,  # 0 = front, 1 = back
}
lock = Lock()


def make_callback(is_front: bool):
	"""Fabrique un callback pour l'avant ou l'arrière."""

	def _callback(outdata, frames, time, status):
		if status:
			print(status)

		with lock:
			phase = state["phase"]
			pan = state["pan"]
			depth = state["depth"]

		t = (np.arange(frames) + phase) / FS
		mono = AMP * np.sin(2 * np.pi * FREQ * t)

		pan_l = np.sqrt(1 - pan)
		pan_r = np.sqrt(pan)

		front_gain = 1.0 - depth
		back_gain = depth
		gain = front_gain if is_front else back_gain

		left = mono * pan_l * gain
		right = mono * pan_r * gain

		outdata[:] = np.column_stack((left, right)).astype(np.float32)

		with lock:
			state["phase"] = phase + frames

	return _callback


def clamp01(x: float) -> float:
	return max(0.0, min(1.0, x))


def main():
	pygame.init()
	WIDTH, HEIGHT = 900, 360
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Panoramique 4.0 (A/D gauche-droite, W/S avant-arrière)")
	clock = pygame.time.Clock()

	x = WIDTH * 0.5
	y = HEIGHT * 0.5
	speed = 6

	# Préparer les streams avant / arrière
	front_stream = sd.OutputStream(
		device=FRONT_DEVICE_ID,
		samplerate=FS,
		blocksize=BLOCK,
		channels=2,
		dtype="float32",
		callback=make_callback(is_front=True),
	)

	rear_stream = sd.OutputStream(
		device=REAR_DEVICE_ID,
		samplerate=FS,
		blocksize=BLOCK,
		channels=2,
		dtype="float32",
		callback=make_callback(is_front=False),
	)

	try:
		front_stream.start()
		rear_stream.start()
	except Exception as exc:  # Sécurité pour erreurs de device
		print(f"Erreur ouverture flux audio : {exc}")
		front_stream.close()
		rear_stream.close()
		return

	running = True
	while running:
		clock.tick(60)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
				running = False

		keys = pygame.key.get_pressed()
		if keys[pygame.K_a]:
			x -= speed
		if keys[pygame.K_d]:
			x += speed
		if keys[pygame.K_w]:
			y -= speed
		if keys[pygame.K_s]:
			y += speed

		x = max(0, min(WIDTH, x))
		y = max(0, min(HEIGHT, y))

		with lock:
			state["pan"] = clamp01(x / WIDTH)
			state["depth"] = clamp01(y / HEIGHT)

		# Affichage minimal
		screen.fill((28, 28, 32))
		pygame.draw.rect(screen, (80, 80, 90), (0, HEIGHT * 0.5, WIDTH, 2))
		pygame.draw.circle(screen, (0, 190, 255), (int(x), int(y)), 12)
		pygame.display.flip()

	front_stream.stop()
	rear_stream.stop()
	front_stream.close()
	rear_stream.close()
	pygame.quit()


if __name__ == "__main__":
	main()
