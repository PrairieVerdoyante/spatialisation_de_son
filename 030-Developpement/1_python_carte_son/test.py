"""
    Permet de retrouver le numéro de la carte son, à adapter ensuite dans les fichiers.
    Exemple de sortie valide: 30 Line (Steinberg UR44C-1), Windows WDM-KS (0 in, 2 out)
    sd.default.device = (None, 30)   # ligne à adapter
"""
import sounddevice as sd

print(sd.query_devices())