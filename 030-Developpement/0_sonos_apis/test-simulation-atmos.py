#!/usr/bin/env python3
"""
Simulation "Atmos-like" simple :
- plusieurs objets audio (mono .wav)
- spatialisation vers 4 enceintes (FL, FR, RL, RR)
- visualisation VPython (optionnelle)
"""

import numpy as np
import soundfile as sf
import sounddevice as sd
import math
import time
from vpython import sphere, vector, rate, scene, color

# ----------------------------
# Configuration
# ----------------------------
OBJECT_FILES = [
    "voice.wav",     # objet 0 (chemin vers fichier mono)
    "fx.wav",        # objet 1
    # ajoute d'autres fichiers si besoin
]

SAMPLE_RATE = 48000           # échantillonnage cible (doit correspondre aux fichiers)
BLOCK_SIZE = 1024             # bloc de traitement / latence
LOOP = True                   # rejouer en boucle
VOLUME_MASTER = 0.8           # gain global (0.0 - 1.0)

# Positions enceintes (unité arbitraire, ex: mètres)
SPEAKER_POS = {
    "FL": np.array([-2.0, 0.0,  2.0]),
    "FR": np.array([ 2.0, 0.0,  2.0]),
    "RL": np.array([-2.0, 0.0, -2.0]),
    "RR": np.array([ 2.0, 0.0, -2.0]),
}
SPK_KEYS = ["FL", "FR", "RL", "RR"]
N_CHANNELS = len(SPK_KEYS)    # 4

# Paramètres de spatialisation
MAX_AUDIBLE_DISTANCE = 8.0    # distance à laquelle le son devient négligeable
MIN_GAIN = 0.0
EPS = 1e-6

# ----------------------------
# Chargement des objets audio
# ----------------------------
class AudioObject:
    def __init__(self, filename):
        data, sr = sf.read(filename, dtype='float32')
        if data.ndim > 1:
            # prendre le premier canal si fichier stéréo
            data = data[:, 0]
        if sr != SAMPLE_RATE:
            raise RuntimeError(f"Sample rate mismatch: {filename} ({sr} Hz) != {SAMPLE_RATE} Hz")
        self.data = data
        self.len = len(data)
        self.pos = np.array([0.0, 0.0, 0.0])   # position 3D de l'objet (modifiable)
        self.play_idx = 0                      # index courant pour lecture
        self.loop = True

objects = []
for fname in OBJECT_FILES:
    objects.append(AudioObject(fname))

# exemple de positions initiales des objets (tu peux les animer)
objects[0].pos = np.array([0.0, 0.0, 3.0])   # devant
if len(objects) > 1:
    objects[1].pos = np.array([2.5, 0.5, -1.0])  # côté/derrière

# ----------------------------
# VPython - visualisation simple
# ----------------------------
scene.title = "Simulation audio-objet (4 canaux)"
scene.width = 800
scene.height = 600
scene.background = vector(0.1, 0.1, 0.1)
aud_center = sphere(pos=vector(0,0,0), radius=0.1, color=color.white)
spk_spheres = {}
for k in SPK_KEYS:
    p = SPEAKER_POS[k]
    spk_spheres[k] = sphere(pos=vector(p[0], p[1], p[2]), radius=0.15, color=color.red)
obj_spheres = []
for obj in objects:
    obj_spheres.append(sphere(pos=vector(*obj.pos), radius=0.25, color=color.cyan, make_trail=True))

# ----------------------------
# Fonctions utilitaires de spatialisation
# ----------------------------
def distance(a, b):
    return np.linalg.norm(a - b)

def compute_gains_for_object(obj_pos):
    """
    Retourne un vecteur de gains normalisés (N_CHANNELS) pour un objet situé en obj_pos.
    On combine attenuation par distance + panning directionnel simple.
    """
    gains = np.zeros(N_CHANNELS, dtype=np.float32)
    # calcul distance -> attenuation (inverse distance law avec clamp)
    dists = np.array([distance(obj_pos, SPEAKER_POS[k]) for k in SPK_KEYS])
    # clamp et convert to gain: plus proche => plus grand
    # simple modèle: gain = 1 / (d + 1) ; puis normaliser
    raw = 1.0 / (dists + 1.0 + EPS)
    # fade-out en fonction d max audible
    raw *= (1.0 - np.clip(dists / MAX_AUDIBLE_DISTANCE, 0.0, 1.0))
    # si tout est nul, renvoyer zéros
    if np.all(raw <= 1e-8):
        return gains
    # panning directionnel (accentuer enceintes vers lesquelles l'objet "regarde")
    # on normalise raw pour garder balance relative
    gains = raw / (np.max(raw) + EPS)
    # petite normalisation finale (on veut que la somme ne dépasse pas 1)
    s = gains.sum()
    if s > 0:
        gains = gains / s
    return gains

# ----------------------------
# Mixer en temps réel
# ----------------------------
def callback(outdata, frames, time_info, status):
    """
    outdata shape: (frames, N_CHANNELS)
    On remplit outdata avec le mix des objets.
    """
    # buffer initial
    mix = np.zeros((frames, N_CHANNELS), dtype=np.float32)

    for i_obj, obj in enumerate(objects):
        # extraire bloc de samples mono
        idx0 = obj.play_idx
        idx1 = idx0 + frames
        # récupérer les samples (gérer boucle)
        if idx1 <= obj.len:
            samples = obj.data[idx0:idx1]
            obj.play_idx = idx1
            if obj.play_idx >= obj.len and obj.loop:
                obj.play_idx = 0
        else:
            # partie jusqu'à la fin
            part1 = obj.data[idx0:obj.len]
            remaining = frames - len(part1)
            if obj.loop:
                # reprendre depuis le début
                part2 = obj.data[0:remaining]
                samples = np.concatenate((part1, part2))
                obj.play_idx = remaining
            else:
                # pad de zéros
                part2 = np.zeros(remaining, dtype=np.float32)
                samples = np.concatenate((part1, part2))
                obj.play_idx = obj.len

        # calcul des gains (constantes sur le bloc pour simplicité)
        gains = compute_gains_for_object(obj.pos)  # vecteur N_CHANNELS
        # appliquer les gains au signal mono pour obtenir N_CHANNELS
        # samples.shape == (frames,)
        # broadcast multiplication
        # on applique aussi un facteur global par objet si besoin (1.0 par défaut)
        obj_gain = 1.0
        for ch in range(N_CHANNELS):
            mix[:, ch] += samples * (gains[ch] * obj_gain)

    # appliquer master volume et clamp (-1, +1)
    mix *= VOLUME_MASTER
    mix = np.clip(mix, -1.0, 1.0)
    outdata[:] = mix

# ----------------------------
# Lancement de la sortie audio + animation
# ----------------------------
print("Ouverture du flux audio...")
stream = sd.OutputStream(
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    channels=N_CHANNELS,
    dtype='float32',
    callback=callback,
)

stream.start()
print("Flux démarré. Press Ctrl+C to stop.")

# petite boucle d'animation : déplacer les objets (ex : rotation circulaire)
t = 0.0
try:
    while True:
        rate(60)  # met à jour la visualisation VPython
        # exemple d'animation : faire tourner le premier objet autour de l'auditeur
        # objet 0 tourne devant
        if len(objects) >= 1:
            R = 3.0
            speed = 0.8
            objects[0].pos[0] = R * math.cos(t * speed)
            objects[0].pos[2] = R * math.sin(t * speed)
            obj_spheres[0].pos = vector(*objects[0].pos)
        # objet 1, mouvement différent
        if len(objects) >= 2:
            R2 = 2.0
            speed2 = -0.5
            objects[1].pos[0] = R2 * math.cos(t * speed2) + 1.0
            objects[1].pos[2] = R2 * math.sin(t * speed2) - 1.0
            objects[1].pos[1] = 0.5 * math.sin(t * 0.7)  # variation en hauteur
            obj_spheres[1].pos = vector(*objects[1].pos)
        t += 0.02

except KeyboardInterrupt:
    print("Arrêt demandé par l'utilisateur...")

finally:
    stream.stop()
    stream.close()
    print("Flux audio fermé.")

#pip install numpy soundfile sounddevice vpython