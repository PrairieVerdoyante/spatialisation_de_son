import numpy as np
import sounddevice as sd
import time

DEVICE_1 = 10  # 10 Line (2- Steinberg UR44C), Windows DirectSound (0 in, 2 out) (voir test.py)
#DEVICE_2 = 22

fs = 44100
duration = 1.5
pause = 1.0

frequency = 440
amplitude = 0.3

t = np.linspace(0, duration, int(fs * duration), endpoint=False)
signal = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)

left_only = np.column_stack((signal, np.zeros_like(signal)))
right_only = np.column_stack((np.zeros_like(signal), signal))

def play_stereo_sequence(device_id):
    sd.default.device = (None, device_id)
    
    dev = sd.query_devices(device_id)
    nch = dev['max_output_channels']
    
    if nch >= 2:
        print(f"Device {device_id}: Playing LEFT")
        sd.play(left_only, fs)
        sd.wait()
        
        time.sleep(pause)
        
        print(f"Device {device_id}: Playing RIGHT")
        sd.play(right_only, fs)
        sd.wait()

play_stereo_sequence(DEVICE_1)
time.sleep(2)
#play_stereo_sequence(DEVICE_2)
