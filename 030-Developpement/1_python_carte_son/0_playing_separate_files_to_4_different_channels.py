"""Utilise la librairie pyo pour utiliser 4 sorties.
"""
import sounddevice as sd

devices = sd.query_devices()
print("=== Tous les périphériques audio ===")
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']}  (in={dev['max_input_channels']}, out={dev['max_output_channels']})")

# Filtrer uniquement ceux qui ont des sorties
print("\n=== Périphériques avec sorties > 0 ===")
for i, dev in enumerate(devices):
    if dev["max_output_channels"] > 0:
        print(f"{i}: {dev['name']}  (out={dev['max_output_channels']})")

print("\nAppareil par défaut (out):", sd.default.device[1])

